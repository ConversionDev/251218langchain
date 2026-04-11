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
    backfill_missing_profile_fields,
    build_embedding_content,
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
from domain.hub.repositories.performance_record_repository import (  # type: ignore
    fill_embeddings_for_performance_records,
    list_by_employee as repo_list_performance_by_employee,
)
from domain.hub.repositories.audit_log_repository import create_log as repo_create_audit_log  # type: ignore

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
    resumeText: str | None = Field(None, description="이력서 원본 추출 텍스트 (ATS AI 분석용)")
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


@router.get("/check-resume-hash", response_model=Dict[str, Any])
def check_resume_hash(
    resume_hash: str = "",
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """이력서 파일 해시로 이미 등록된 지원인지 확인. 지원 페이지에서 중복 제출 방지용."""
    h = (resume_hash or "").strip()
    if not h:
        return {"exists": False}
    existing = repo_find_by_resume_hash(db, h)
    if existing:
        return {"exists": True, "existing": existing}
    return {"exists": False}


class EmbeddingRequest(BaseModel):
    """직원 임베딩 갱신 요청. id 없으면 embedding이 비어 있는 전체 직원 대상."""

    id: Optional[str] = Field(None, description="직원 ID. 없으면 전체 갱신")
    includeExisting: bool = Field(False, description="true면 기존 embedding 보유 직원까지 재생성")
    regenerateContent: bool = Field(False, description="true면 기존 embedding_content도 강제로 재작성")
    useExaonePersona: bool = Field(False, description="true면 EXAONE으로 직원 페르소나 요약 생성 후 임베딩")


class ProfileBackfillRequest(BaseModel):
    """기존 직원 결측 프로필(성별/나이/교육시간) 일괄 보정 요청."""

    dryRun: bool = Field(True, description="true면 DB 반영 없이 예상 결과만 반환")
    seed: int = Field(42, description="랜덤 시드(재현 가능성 보장)")


def _build_persona_prompt(profile_text: str) -> str:
    return (
        "다음 직원 정보를 RAG 검색 최적화용 '직원 역량 페르소나'로 8~12문장 내외 한국어 평문으로 요약하세요. "
        "반드시 포함: 핵심역량, 업무도메인, 실무강점, 협업스타일, 교육/학습 포인트, 추천 질문 키워드. "
        "JSON/마크다운 없이 문장 텍스트만 출력하세요.\n\n"
        f"[직원 정보]\n{profile_text}"
    )


def _generate_persona_text(profile_text: str) -> str:
    """EXAONE 페르소나 생성. 실패 시 기본 텍스트 반환."""
    try:
        from domain.hub.llm.exaone_adapter import generate_text  # type: ignore

        out = generate_text(_build_persona_prompt(profile_text), max_tokens=512, temperature=0.3)
        txt = (out or "").strip()
        if not txt or txt.startswith("[ExaOne 오류]"):
            return profile_text
        return txt
    except Exception:
        return profile_text


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
        content_override = None
        if body.useExaonePersona:
            one = repo_get_by_id(db, body.id)
            if not one:
                raise HTTPException(status_code=404, detail="Employee not found")
            profile = (
                f"직원 ID: {one.get('id','')}. 이름: {one.get('name','')}. 직급: {one.get('jobTitle') or ''}. "
                f"부서: {one.get('department') or ''}. 고용형태: {one.get('employmentType') or ''}. "
                f"교육훈련: {one.get('trainingHours') if one.get('trainingHours') is not None else '미기재'}시간. "
                f"이력서: {one.get('resume') or {}}."
            )
            content_override = _generate_persona_text(profile)
        ok = update_one_employee_embedding(
            db,
            body.id,
            emb,
            embedding_content_override=content_override,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Employee not found or embed failed")
        return {"updated": 1, "id": body.id, "useExaonePersona": body.useExaonePersona}

    content_builder = None
    if body.useExaonePersona:
        def _content_builder(row: Any) -> str:
            base_profile = build_embedding_content(row)
            return _generate_persona_text(base_profile)

        content_builder = _content_builder

    n = fill_embeddings_for_employees(
        db,
        emb,
        include_existing=body.includeExisting,
        force_rebuild_content=body.regenerateContent,
        content_builder=content_builder,
    )
    perf_n = 0
    try:
        perf_n = fill_embeddings_for_performance_records(
            db, emb, include_existing=body.includeExisting,
        )
    except Exception as pe:
        logger.warning("performance_records 임베딩 생성 중 오류 (스키마 미설정 가능): %s", pe)
    return {
        "updated": n,
        "performanceUpdated": perf_n,
        "includeExisting": body.includeExisting,
        "regenerateContent": body.regenerateContent,
        "useExaonePersona": body.useExaonePersona,
    }


@router.post("/profile-backfill", response_model=Dict[str, Any])
def backfill_employee_profiles(
    body: ProfileBackfillRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    기존 직원 결측치(gender, age, training_hours) 일괄 보정.
    - dryRun=true: 미리보기만 반환
    - dryRun=false: DB 저장
    """
    try:
        result = backfill_missing_profile_fields(
            db,
            dry_run=body.dryRun,
            seed=body.seed,
        )
        if not body.dryRun and result.get("updated"):
            _write_audit_log(
                db,
                request=request,
                action="bulk_backfill_profile",
                entity_id="employees",
                before_data={"mode": "missing_only"},
                after_data=result,
                reason="backfill missing gender/age/training_hours",
            )
        return result
    except Exception as e:
        logger.exception("직원 프로필 결측 보정 실패: %s", e)
        raise HTTPException(status_code=500, detail="직원 프로필 결측 보정 중 오류가 발생했습니다.")


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

    # 1) 이력서 텍스트 — 원본 추출 텍스트 우선, 없으면 구조화 데이터로 대체
    stored_resume_text = (one.get("resumeText") or "").strip()
    resume = one.get("resume")
    resume_text = stored_resume_text if stored_resume_text else (
        _resume_dict_to_text(resume) if isinstance(resume, dict) else ""
    )

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
    - 지원일: 신입(employmentType=new_hire)인 경우 등록(업로드) 시점의 서버 시각(UTC)으로 저장.
    - 입사일: 신입은 입사 확정 전까지 비워 둠(화면에서 입사 확정 시 설정)."""
    try:
        data = payload.model_dump(exclude_unset=False)
        if data.get("employmentType") == "new_hire":
            data["applicationDate"] = datetime.now(timezone.utc)
            data["joinedAt"] = None  # 입사일은 입사 확정 시에만 설정
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
    except Exception as e:
        logger.exception("직원 생성 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail="지원서 저장 중 오류가 발생했습니다. DB 연결과 서버 로그를 확인해 주세요.",
        )


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
