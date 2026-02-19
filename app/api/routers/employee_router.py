"""직원 CRUD API — Neon employees 테이블.

GET /api/employees: 목록
GET /api/employees/{id}: 단건
POST /api/employees: 생성
PUT /api/employees/{id}: 수정
DELETE /api/employees/{id}: 삭제
POST /api/employees/embedding: 직원 임베딩 갱신(전체 또는 지정 id). RAG 검색용 pgvector 갱신.
이력서 분석은 /api/resume/analyze 유지.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from core.database import get_db  # type: ignore
from domain.hub.repositories.employee_repository import (  # type: ignore
    create as repo_create,
    delete as repo_delete,
    fill_embeddings_for_employees,
    find_by_resume_hash as repo_find_by_resume_hash,
    get_by_id as repo_get_by_id,
    list_all as repo_list_all,
    update as repo_update,
    update_one_employee_embedding,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["Employees"])


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

    model_config = {"extra": "allow"}


@router.get("", response_model=List[Dict[str, Any]])
def list_employees(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """직원 목록 (Neon)."""
    return repo_list_all(db)


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


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_employee(payload: EmployeePayload, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원 생성. 동일 이력서(resumeFileHash)가 이미 있으면 409(추가하지 않음)."""
    try:
        data = payload.model_dump(exclude_unset=False)
        return repo_create(db, data)
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
def update_employee(employee_id: str, payload: EmployeePayload, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원 수정. id는 path 기준."""
    data = payload.model_dump(exclude_unset=True)
    data["id"] = employee_id
    result = repo_update(db, employee_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: str, db: Session = Depends(get_db)) -> None:
    """직원 삭제."""
    if not repo_delete(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
