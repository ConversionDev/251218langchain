"""Disclosure(ISO 30414) RAG 적재 상태 조회 및 공시 기여도 예측 API.

- 신입/지원자: 입사 시 인적자본 공시 지표에 기여할 잠재력 분석 + 면접 시 확인 질문 가이드.
- 비동기: POST /check → job_id, GET /check/result/{job_id} 폴링.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from application.disclosure.disclosure_service import (  # type: ignore
    DisclosureCheckRequest,
    DisclosureCheckResponse,
    DisclosureService,
    DisclosureStatusResponse,
    EmbeddingRunResponse,
)
from core.database import SessionLocal, get_db  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disclosure", tags=["Disclosure (공시 기여도 예측)"])

_check_jobs: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# 적재 상태
# ---------------------------------------------------------------------------

@router.get("/status", response_model=DisclosureStatusResponse)
async def get_disclosure_status(db: Session = Depends(get_db)) -> DisclosureStatusResponse:
    """ISO 30414 문서가 disclosures 테이블에 적재되었는지 조회."""
    return DisclosureService(db).get_status()


# ---------------------------------------------------------------------------
# 임베딩 실행
# ---------------------------------------------------------------------------

@router.post("/embedding/run", response_model=EmbeddingRunResponse)
async def run_disclosure_embedding(db: Session = Depends(get_db)) -> EmbeddingRunResponse:
    """embedding이 null인 공시 문서에 임베딩을 채웁니다."""
    return DisclosureService(db).run_embedding()


# ---------------------------------------------------------------------------
# 공시 기여도 예측 (비동기 job)
# ---------------------------------------------------------------------------

class DisclosureCheckJobResponse(BaseModel):
    job_id: str = Field(..., description="결과 조회용 작업 ID")


class DisclosureCheckResultResponse(BaseModel):
    status: str = Field(..., description="pending | completed | failed")
    result: Optional[DisclosureCheckResponse] = Field(None)
    error: Optional[str] = Field(None)


def _run_check_background(job_id: str, payload: DisclosureCheckRequest) -> None:
    """백그라운드에서 공시 확인 실행 후 _check_jobs 갱신."""
    db = SessionLocal()
    try:
        result = DisclosureService(db).run_check(payload)
        _check_jobs[job_id] = {"status": "completed", "result": result, "error": None}
        logger.info("[DisclosureCheck] job_id=%s completed", job_id)
    except Exception as e:
        logger.exception("[DisclosureCheck] job_id=%s failed: %s", job_id, e)
        _check_jobs[job_id] = {"status": "failed", "result": None, "error": str(e)}
    finally:
        db.close()


@router.post("/check", response_model=DisclosureCheckJobResponse)
async def post_disclosure_check(
    body: DisclosureCheckRequest,
    background_tasks: BackgroundTasks,
) -> DisclosureCheckJobResponse:
    """공시 기여도 예측을 비동기로 시작. job_id로 결과 폴링."""
    job_id = str(uuid.uuid4())
    _check_jobs[job_id] = {"status": "pending", "result": None, "error": None}
    background_tasks.add_task(_run_check_background, job_id, body)
    return DisclosureCheckJobResponse(job_id=job_id)


@router.get("/check/result/{job_id}", response_model=DisclosureCheckResultResponse)
async def get_disclosure_check_result(job_id: str) -> DisclosureCheckResultResponse:
    """비동기 공시 확인 결과 조회 (폴링)."""
    if job_id not in _check_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    entry = _check_jobs[job_id]
    return DisclosureCheckResultResponse(
        status=entry["status"],
        result=entry.get("result"),
        error=entry.get("error"),
    )
