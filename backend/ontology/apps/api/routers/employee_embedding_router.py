"""직원 임베딩·프로필 보정 API.

POST /employees/embedding: RAG용 pgvector 임베딩 갱신
POST /employees/profile-backfill: 결측 프로필(gender/age/training_hours) 일괄 보정
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from api.routers._employee_shared import _write_audit_log  # type: ignore
from core.database import get_db  # type: ignore
from domain.hub.repositories.employee_repository import (  # type: ignore
    backfill_missing_profile_fields,
    build_embedding_content,
    fill_embeddings_for_employees,
    get_by_id as repo_get_by_id,
    update_one_employee_embedding,
)
from domain.hub.repositories.performance_record_repository import (  # type: ignore
    fill_embeddings_for_performance_records,
)

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


def _build_persona_prompt(profile_text: str) -> str:
    return (
        "다음 직원 정보를 RAG 검색 최적화용 '직원 역량 페르소나'로 8~12문장 내외 한국어 평문으로 요약하세요. "
        "반드시 포함: 핵심역량, 업무도메인, 실무강점, 협업스타일, 교육/학습 포인트, 추천 질문 키워드. "
        "JSON/마크다운 없이 문장 텍스트만 출력하세요.\n\n"
        f"[직원 정보]\n{profile_text}"
    )


def _generate_persona_text(profile_text: str) -> str:
    """EXAONE 페르소나 생성. 실패 시 원본 텍스트 반환."""
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
        ok = update_one_employee_embedding(db, body.id, emb, embedding_content_override=content_override)
        if not ok:
            raise HTTPException(status_code=404, detail="Employee not found or embed failed")
        return {"updated": 1, "id": body.id, "useExaonePersona": body.useExaonePersona}

    content_builder = None
    if body.useExaonePersona:
        def _content_builder(row: Any) -> str:
            return _generate_persona_text(build_embedding_content(row))
        content_builder = _content_builder

    n = fill_embeddings_for_employees(
        db, emb,
        include_existing=body.includeExisting,
        force_rebuild_content=body.regenerateContent,
        content_builder=content_builder,
    )
    perf_n = 0
    try:
        perf_n = fill_embeddings_for_performance_records(db, emb, include_existing=body.includeExisting)
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
    """기존 직원 결측치(gender, age, training_hours) 일괄 보정.
    dryRun=true: 미리보기만 반환 / dryRun=false: DB 저장.
    """
    try:
        result = backfill_missing_profile_fields(db, dry_run=body.dryRun, seed=body.seed)
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
