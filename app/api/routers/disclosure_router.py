"""Disclosure(ISO 30414) RAG 적재 상태 조회 및 공시 기준 적합 여부 판단 API.

공시 기준 확인은 비동기: POST /check → job_id 반환, GET /check/result/{job_id} 로 폴링.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from core.config import get_settings  # type: ignore
from core.database.connection import get_vector_count  # type: ignore
from core.database.vector_store import get_vector_store  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disclosure", tags=["Disclosure (ISO 30414)"])

# 비동기 공시 확인 작업 결과 저장 (job_id -> { status, result?, error? })
_check_jobs: Dict[str, Dict[str, Any]] = {}


class DisclosureStatusResponse(BaseModel):
    """ISO 30414 disclosure 컬렉션 적재 상태."""

    ingested: bool = Field(..., description="학습(적재) 완료 여부")
    document_count: int = Field(..., description="벡터로 저장된 문서(청크) 개수")


class DisclosureCheckRequest(BaseModel):
    """공시 기준 적합 여부 판단 요청 (직원/이력서 요약)."""

    name: str = Field("", description="이름")
    job_title: str = Field("", description="직급")
    department: str = Field("", description="부서")
    email: Optional[str] = Field(None, description="이메일")
    gender: Optional[str] = Field(None, description="성별")
    age_band: Optional[str] = Field(None, description="연령대")
    employment_type: Optional[str] = Field(None, description="고용 형태")
    training_hours: Optional[int] = Field(None, description="연간 교육시간")


class DisclosureCheckResponse(BaseModel):
    """공시 기준 적합 여부 판단 결과."""

    suitable: bool = Field(..., description="적합 여부")
    message: str = Field(..., description="판단 요약")
    suggestions: List[str] = Field(default_factory=list, description="보완 제안 목록")


def _get_embeddings():
    """설정 기반 임베딩 모델 (disclosure 검색용)."""
    settings = get_settings()
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore

    device = getattr(settings, "embedding_device", None) or "cpu"
    return HuggingFaceEmbeddings(
        model_name=settings.default_embedding_model,
        model_kwargs={"device": device},
    )


def _run_disclosure_check(payload: DisclosureCheckRequest) -> DisclosureCheckResponse:
    """RAG(disclosure 컬렉션) + LLM으로 공시 기준 적합 여부 판단."""
    settings = get_settings()
    count = get_vector_count(collection_name=settings.disclosure_collection_name)
    if count == 0:
        return DisclosureCheckResponse(
            suitable=False,
            message="ISO 30414 공시 문서가 아직 적재되지 않았습니다. 먼저 disclosure 적재를 실행해 주세요.",
            suggestions=[],
        )

    employee_summary = (
        f"직원 데이터: 이름 {payload.name}, 직급 {payload.job_title}, 부서 {payload.department}."
    )
    if payload.email:
        employee_summary += f" 이메일 {payload.email}."
    if payload.gender:
        employee_summary += f" 성별 {payload.gender}."
    if payload.age_band:
        employee_summary += f" 연령대 {payload.age_band}."
    if payload.employment_type:
        employee_summary += f" 고용형태 {payload.employment_type}."
    if payload.training_hours is not None:
        employee_summary += f" 연간 교육시간 {payload.training_hours}시간."

    query = (
        "ISO 30414 human capital reporting requirements. "
        "What indicators and categories are required for internal and external reporting?"
    )
    try:
        embeddings = _get_embeddings()
        store = get_vector_store(embeddings, collection_name=settings.disclosure_collection_name)
        retriever = store.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(query)
        context = "\n\n".join(d.page_content[:1500] for d in docs)
    except Exception as e:
        logger.exception("Disclosure 검색 실패: %s", e)
        return DisclosureCheckResponse(
            suitable=False,
            message=f"공시 문서 검색 중 오류: {e}",
            suggestions=[],
        )

    from domain.hub.llm import get_llm  # type: ignore

    system = (
        "You are an expert on ISO 30414 human capital reporting. "
        "Given the following excerpts from ISO 30414 and the employee data, "
        "determine if the employee data is SUITABLE for disclosure reporting (적합) or not (부적합). "
        "Reply in Korean. First line: exactly '적합' or '부적합'. "
        "Then a short message. If 부적합, add a bullet list of suggestions (보완 제안) on the next lines."
    )
    user_text = f"## ISO 30414 관련 문구\n{context}\n\n## 직원 데이터\n{employee_summary}\n\n위 직원 데이터가 ISO 30414 공시 기준에 적합한지 판단해 주세요."

    try:
        llm = get_llm()
        messages = [SystemMessage(content=system), HumanMessage(content=user_text)]
        response = llm.invoke(messages)
        if hasattr(response, "content"):
            text = response.content
        else:
            text = str(response)
    except Exception as e:
        logger.exception("LLM 호출 실패: %s", e)
        return DisclosureCheckResponse(
            suitable=False,
            message=f"판단 생성 중 오류: {e}",
            suggestions=[],
        )

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    suitable = False
    message = ""
    suggestions: List[str] = []
    for i, line in enumerate(lines):
        if "적합" in line and "부적합" not in line:
            suitable = True
        if "부적합" in line:
            suitable = False
        if i == 0:
            message = line
        elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
            suggestions.append(line.lstrip("-•* ").strip())
        elif i > 0 and not message and line:
            message = line
    if not message and lines:
        message = lines[0]
    return DisclosureCheckResponse(suitable=suitable, message=message or text[:200], suggestions=suggestions)


@router.get("/status", response_model=DisclosureStatusResponse)
async def get_disclosure_status() -> DisclosureStatusResponse:
    """ISO 30414 문서가 벡터 스토어에 적재되었는지 조회."""
    settings = get_settings()
    count = get_vector_count(collection_name=settings.disclosure_collection_name)
    return DisclosureStatusResponse(
        ingested=count > 0,
        document_count=count,
    )


class DisclosureCheckJobResponse(BaseModel):
    """비동기 공시 확인 요청 즉시 응답."""

    job_id: str = Field(..., description="결과 조회용 작업 ID")


class DisclosureCheckResultResponse(BaseModel):
    """공시 확인 결과 조회 (폴링)."""

    status: str = Field(..., description="pending | completed | failed")
    result: Optional[DisclosureCheckResponse] = Field(None, description="완료 시 결과")
    error: Optional[str] = Field(None, description="실패 시 오류 메시지")


def _run_check_background(job_id: str, payload: DisclosureCheckRequest) -> None:
    """백그라운드에서 공시 확인 실행 후 _check_jobs 갱신."""
    try:
        result = _run_disclosure_check(payload)
        _check_jobs[job_id] = {"status": "completed", "result": result, "error": None}
        logger.info("[DisclosureCheck] job_id=%s completed", job_id)
    except Exception as e:
        logger.exception("[DisclosureCheck] job_id=%s failed: %s", job_id, e)
        _check_jobs[job_id] = {
            "status": "failed",
            "result": None,
            "error": str(e),
        }


@router.post("/check", response_model=DisclosureCheckJobResponse)
async def post_disclosure_check(
    body: DisclosureCheckRequest,
    background_tasks: BackgroundTasks,
) -> DisclosureCheckJobResponse:
    """공시 기준 적합 여부 판단을 비동기로 시작. job_id로 결과 폴링."""
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
