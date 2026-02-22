"""직원 CRUD API — Neon employees 테이블.

GET /api/employees: 목록
GET /api/employees/{id}: 단건
POST /api/employees: 생성
PUT /api/employees/{id}: 수정
DELETE /api/employees/{id}: 삭제
POST /api/employees/embedding: 직원 임베딩 갱신(전체 또는 지정 id). RAG 검색용 pgvector 갱신.
이력서 분석은 /api/resume/analyze 유지.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from api.services.resume_analyzer import _resume_dict_to_text, analyze_resume_text  # type: ignore
from core.database import get_db  # type: ignore
from domain.hub.repositories.employee_repository import (  # type: ignore
    create as repo_create,
    delete as repo_delete,
    fill_embeddings_for_employees,
    find_by_resume_hash as repo_find_by_resume_hash,
    get_by_id as repo_get_by_id,
    get_next_id as repo_get_next_id,
    list_all as repo_list_all,
    list_paginated as repo_list_paginated,
    update as repo_update,
    update_one_employee_embedding,
)
from domain.hub.repositories.audit_log_repository import create_log as repo_create_audit_log  # type: ignore
from domain.hub.repositories.performance_record_repository import (  # type: ignore
    list_by_employee as repo_list_performance_by_employee,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["Employees"])


def _resolve_actor(request: Request) -> str:
    actor = (request.headers.get("x-actor") or "").strip()
    if actor:
        return actor
    return "system"


def _write_audit_log(
    db: Session,
    *,
    request: Request,
    action: str,
    entity_id: str,
    before_data: Optional[Dict[str, Any]] = None,
    after_data: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
) -> None:
    try:
        repo_create_audit_log(
            db,
            entity_type="employee",
            entity_id=entity_id,
            action=action,
            actor=_resolve_actor(request),
            reason=reason,
            before_data=before_data,
            after_data=after_data,
        )
    except Exception as e:
        logger.warning("감사로그 저장 실패 action=%s entity_id=%s err=%s", action, entity_id, e)


class EmployeePayload(BaseModel):
    """직원 생성/수정 요청 (프론트 Employee 호환 camelCase)."""

    id: str = Field(..., description="직원 ID")
    name: str = Field("", description="이름")
    jobTitle: str = Field("", description="직급")
    department: str = Field("", description="부서")
    email: str | None = None
    applicationDate: str | None = Field(None, description="지원일 YYYY-MM-DD (지원서 제출일)")
    joinedAt: str | None = Field(None, description="입사일 YYYY-MM-DD (입사 확정 후 설정)")
    successDna: Dict[str, Any] | None = None
    behavioralDna: Dict[str, Any] | None = None
    behavioralSource: str | None = None
    behavioralSourceItems: List[Dict[str, Any]] | None = None
    disclosureMetrics: Dict[str, Any] | None = None
    gender: str | None = None
    age: int | None = None
    employmentType: str | None = None
    trainingHours: int | None = None
    resume: Dict[str, Any] | None = None
    resumeFileHash: str | None = Field(None, description="이력서 파일 SHA-256, 동일 이력서 중복 방지")
    matchedDepartment: str | None = None
    status: str | None = Field(None, description="채용 상태: pending|screening|hired|rejected")
    successDnaReason: str | None = Field(None, description="평가 근거 (수동 수정 가능)")
    rejectionReason: str | None = Field(None, description="탈락 사유 (탈락 처리 시 입력)")

    model_config = {"extra": "allow"}


class PaginatedEmployeesResponse(BaseModel):
    """페이징된 직원 목록 응답."""

    items: List[Dict[str, Any]]
    total: int
    page: int
    pageSize: int


@router.get("", response_model=None)
def list_employees(
    db: Session = Depends(get_db),
    page: Optional[int] = None,
    pageSize: Optional[int] = None,
    employmentType: Optional[str] = None,
) -> List[Dict[str, Any]] | PaginatedEmployeesResponse:
    """직원 목록. page 또는 pageSize가 있으면 페이징 응답(items,total,page,pageSize), 없으면 전체 목록."""
    if page is not None or pageSize is not None:
        p = max(1, page or 1)
        ps = max(1, min(100, pageSize or 20))
        items, total = repo_list_paginated(db, page=p, page_size=ps, employment_type=employmentType)
        return PaginatedEmployeesResponse(items=items, total=total, page=p, pageSize=ps)
    return repo_list_all(db)


@router.get("/next-id", response_model=Dict[str, Any])
def get_next_employee_id(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """다음 직원 ID 제안 (직원 추가 폼용)."""
    return {"nextId": repo_get_next_id(db)}


class EmbeddingRequest(BaseModel):
    """직원 임베딩 갱신 요청. id 없으면 embedding이 비어 있는 전체 직원 대상."""

    id: Optional[str] = Field(None, description="직원 ID. 없으면 전체 갱신")


@router.post("/embedding")
def refresh_employee_embeddings(
    body: EmbeddingRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """직원 RAG용 임베딩 갱신. embedding_content 없으면 자동 생성 후 임베딩. Neon pgvector(HNSW)에 반영."""
    try:
        from domain.shared.embedding import get_disclosure_embedding_model  # type: ignore
        emb = get_disclosure_embedding_model()
    except Exception as e:
        logger.warning("Embedding 모델 로드 실패: %s", e)
        try:
            import fastapi_server  # type: ignore
            fastapi_server.ensure_rag_initialized()
            emb = getattr(fastapi_server, "local_embeddings", None)
        except Exception:
            emb = None
    if not emb:
        raise HTTPException(status_code=503, detail="Embedding model not available")
    if body.id:
        ok = update_one_employee_embedding(db, body.id, emb)
        if not ok:
            raise HTTPException(status_code=404, detail="Employee not found or embed failed")
        return {"updated": 1, "id": body.id}
    n = fill_embeddings_for_employees(db, emb)
    return {"updated": n}


@router.get("/{employee_id}", response_model=Dict[str, Any])
def get_employee(employee_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원 단건 조회."""
    one = repo_get_by_id(db, employee_id)
    if not one:
        raise HTTPException(status_code=404, detail="Employee not found")
    return one


@router.post("/{employee_id}/analyze", response_model=Dict[str, Any])
async def analyze_employee_resume(
    employee_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """직원 AI 분석.
    - 신입(new_hire): resume 중심 분석 후 status → screening
    - 기존 직원(regular): resume + 성과활동(performance_records) 기반 분석 (status 변경 없음)
    """
    one = repo_get_by_id(db, employee_id)
    if not one:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 1) 이력서 텍스트(선택)
    resume = one.get("resume")
    resume_text = _resume_dict_to_text(resume) if isinstance(resume, dict) else ""

    # 2) 성과 활동 텍스트(선택)
    perf_rows = repo_list_performance_by_employee(db, employee_id, limit=50)
    perf_lines: List[str] = []
    for r in perf_rows:
        period = str(r.get("period") or "").strip()
        text_type = str(r.get("textType") or "").strip()
        content = str(r.get("content") or "").strip()
        if not content:
            continue
        perf_lines.append(f"[{period}][{text_type}] {content}")
    perf_text = "\n".join(perf_lines)

    # 실무형: 기존 직원은 이력서가 없어도 성과활동만으로 분석 허용
    text_parts = []
    if resume_text and len(resume_text.strip()) >= 10:
        text_parts.append("## 이력/프로필\n" + resume_text.strip())
    if perf_text and len(perf_text.strip()) >= 10:
        text_parts.append("## 성과활동\n" + perf_text.strip())
    text = "\n\n".join(text_parts)
    if not text or len(text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="분석 가능한 텍스트가 없습니다. (resume 또는 성과활동 기록 필요)",
        )

    try:
        result = await asyncio.to_thread(analyze_resume_text, text, True)  # ats_only=True: 경량 프롬프트·캐시
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("AI 분석 실패 employee_id=%s: %s", employee_id, e)
        raise HTTPException(status_code=500, detail=f"AI 분석 중 오류: {e}")
    payload: Dict[str, Any] = {
        "successDna": result.get("successDna"),
        "successDnaReason": result.get("successDnaReason"),
    }
    # 신입만 screening으로 전환. 기존 직원 상태는 유지.
    if (one.get("employmentType") or "").strip().lower() == "new_hire":
        payload["status"] = "screening"

    updated = repo_update(db, employee_id, payload)
    _write_audit_log(
        db,
        request=request,
        action="analyze",
        entity_id=employee_id,
        before_data=one,
        after_data=updated or one,
        reason="ai analyze",
    )
    return updated or one


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_employee(
    payload: EmployeePayload,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any] | JSONResponse:
    """직원 생성. 동일 이력서(resumeFileHash)가 이미 있으면 409(추가하지 않음).
    신입 지원(employmentType=new_hire)인 경우 제출일시는 서버 시각(UTC)으로 저장."""
    try:
        data = payload.model_dump(exclude_unset=False)
        if data.get("employmentType") == "new_hire":
            data["applicationDate"] = datetime.now(timezone.utc)
            # 지원 접수 시 항상 미검토. AI 분석 API 호출 후에만 screening(심사 중)으로 변경됨.
            data["status"] = "pending"
            # 지원서 제출 시점에는 Success DNA/평가 근거 없음. AI 분석 후에만 저장됨.
            data["successDna"] = None
            data["successDnaReason"] = None
        created = repo_create(db, data)
        _write_audit_log(
            db,
            request=request,
            action="create",
            entity_id=created.get("id") or payload.id,
            after_data=created,
            reason="create employee",
        )
        return created
    except ValueError as e:
        if str(e) == "ALREADY_EXISTS":
            resume_hash = (payload.resumeFileHash or "").strip()
            existing = repo_find_by_resume_hash(db, resume_hash) if resume_hash else None
            return JSONResponse(
                status_code=409,
                content={"detail": "동일한 이력서가 이미 등록되어 있습니다", "existing": existing or {}},
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{employee_id}", response_model=Dict[str, Any])
def update_employee(
    employee_id: str,
    payload: EmployeePayload,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """직원 수정. id는 path 기준."""
    data = payload.model_dump(exclude_unset=True)
    data["id"] = employee_id
    before = repo_get_by_id(db, employee_id)
    result = repo_update(db, employee_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    _write_audit_log(
        db,
        request=request,
        action="update",
        entity_id=employee_id,
        before_data=before,
        after_data=result,
        reason="update employee",
    )
    return result


@router.delete("/{employee_id}", status_code=204)
def delete_employee(
    employee_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """직원 삭제."""
    before = repo_get_by_id(db, employee_id)
    if not repo_delete(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    _write_audit_log(
        db,
        request=request,
        action="delete",
        entity_id=employee_id,
        before_data=before,
        after_data=None,
        reason="delete employee",
    )
