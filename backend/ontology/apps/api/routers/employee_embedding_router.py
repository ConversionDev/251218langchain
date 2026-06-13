"""직원 임베딩·프로필 보정 API.

POST /employees/embedding: RAG용 pgvector 임베딩 갱신
POST /employees/profile-backfill: 결측 프로필(gender/age/training_hours) 일괄 보정
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from application.shared.audit_service import write_audit_log  # type: ignore
from application.employee.employee_service import EmployeeService  # type: ignore
from core.database import get_db  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Employees"])


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


def _load_embedding_model() -> Any:
    try:
        from domain.shared.embedding import get_disclosure_embedding_model  # type: ignore
        emb = get_disclosure_embedding_model()
        if emb:
            return emb
    except Exception as e:
        logger.warning("Embedding 모델 로드 실패: %s", e)
    try:
        import fastapi_server  # type: ignore
        fastapi_server.ensure_rag_initialized()
        return getattr(fastapi_server, "local_embeddings", None)
    except Exception:
        return None


@router.post("/embedding")
def refresh_employee_embeddings(
    body: EmbeddingRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """직원 RAG용 임베딩 갱신. embedding_content 없으면 자동 생성 후 임베딩. Neon pgvector(HNSW)에 반영."""
    emb = _load_embedding_model()
    if not emb:
        raise HTTPException(status_code=503, detail="Embedding model not available")

    svc = EmployeeService(db)
    try:
        return svc.refresh_embedding(
            emb,
            employee_id=body.id,
            include_existing=body.includeExisting,
            force_rebuild_content=body.regenerateContent,
            use_exaone_persona=body.useExaonePersona,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/profile-backfill", response_model=Dict[str, Any])
def backfill_employee_profiles(
    body: ProfileBackfillRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """기존 직원 결측치(gender, age, training_hours) 일괄 보정.
    dryRun=true: 미리보기만 반환 / dryRun=false: DB 저장.
    """
    try:
        result = EmployeeService(db).backfill_profiles(dry_run=body.dryRun, seed=body.seed)
        if not body.dryRun and result.get("updated"):
            write_audit_log(
                db,
                request=request,
                entity_type="employee",
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
