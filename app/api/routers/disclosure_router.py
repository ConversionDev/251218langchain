"""Disclosure(ISO 30414) RAG 적재 상태 조회 및 공시 기여도 예측 API.

- 신입/지원자: 입사 시 인적자본 공시 지표에 기여할 잠재력 분석 + 면접 시 확인 질문 가이드.
- 비동기: POST /check → job_id, GET /check/result/{job_id} 폴링.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from core.database import SessionLocal  # type: ignore
from domain.hub.repositories.disclosure_repository import (  # type: ignore
    get_disclosure_doc_count,
    search_disclosures,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disclosure", tags=["Disclosure (공시 기여도 예측)"])

# 비동기 공시 확인 작업 결과 저장 (job_id -> { status, result?, error? })
_check_jobs: Dict[str, Dict[str, Any]] = {}


class DisclosureStatusResponse(BaseModel):
    """ISO 30414 disclosure 컬렉션 적재 상태."""

    ingested: bool = Field(..., description="학습(적재) 완료 여부")
    document_count: int = Field(..., description="벡터로 저장된 문서(청크) 개수")


class DisclosureCheckRequest(BaseModel):
    """공시 기여도 예측 요청 (지원자/직원·이력서 요약)."""

    name: str = Field("", description="이름")
    job_title: str = Field("", description="직급")
    department: str = Field("", description="부서")
    email: Optional[str] = Field(None, description="이메일")
    gender: Optional[str] = Field(None, description="성별")
    age_band: Optional[str] = Field(None, description="연령대")
    employment_type: Optional[str] = Field(None, description="고용 형태")
    training_hours: Optional[int] = Field(None, description="연간 교육시간")


class DisclosureCheckResponse(BaseModel):
    """공시 기여도 예측 결과 (가이드라인 포함)."""

    suitable: bool = Field(..., description="기여 잠재력 있음(True) / 보완 필요(False)")
    message: str = Field(..., description="공시 기여도 예측 요약 (다양성·역량 등 잠재적 기여)")
    suggestions: List[str] = Field(default_factory=list, description="면접/확인 시 질문 또는 가이드 목록")


def _run_disclosure_check(payload: DisclosureCheckRequest) -> DisclosureCheckResponse:
    """RAG(disclosures) + LLM으로 공시 기여도 예측 및 면접/확인 가이드 생성."""
    db = SessionLocal()
    try:
        count = get_disclosure_doc_count(db)
        if count == 0:
            return DisclosureCheckResponse(
                suitable=False,
                message="ISO 30414 공시 문서가 아직 적재되지 않았습니다. 먼저 disclosure 적재를 실행해 주세요.",
                suggestions=[],
            )

        employee_summary = (
            f"지원자/직원 데이터: 이름 {payload.name}, 직급 {payload.job_title}, 부서 {payload.department}."
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
        else:
            employee_summary += " (연간 교육시간 미기입)"

        query = (
            "ISO 30414 human capital reporting requirements. "
            "What indicators and categories are required for internal and external reporting?"
        )
        try:
            from domain.shared.embedding import get_embedding_model  # type: ignore

            embeddings = get_embedding_model(use_fp16=True)
            query_vec = embeddings.embed_query(query)
            contents = search_disclosures(db, query_vec, k=5)
            context = "\n\n".join(c[:1500] for c in contents)
        except Exception as e:
            logger.exception("Disclosure 검색 실패: %s", e)
            return DisclosureCheckResponse(
                suitable=False,
                message=f"공시 문서 검색 중 오류: {e}",
                suggestions=[],
            )
    finally:
        db.close()

    from domain.hub.llm import get_llm  # type: ignore

    system = (
        "You are an expert on ISO 30414 human capital reporting. "
        "The input is a CANDIDATE or EMPLOYEE summary (e.g. from a resume). "
        "Your task is to provide a DISCLOSURE CONTRIBUTION PREDICTION (공시 기여도 예측), not to say '부적합' just because some data is missing.\n\n"
        "Reply in Korean only. Use exactly this structure:\n"
        "1) First line: exactly '기여 가능' or '보완 필요'. Use '기여 가능' when the person has clear potential to contribute to disclosure indicators (e.g. diversity, skills). Use '보완 필요' when key data is missing and you recommend follow-up.\n"
        "2) Next paragraph: '공시 기여도 예측' narrative. Explain how this person could contribute to the company's human capital disclosure (e.g. diversity, skills alignment, education). Examples: '이 지원자는 여성/이공계 전공자로 채용 시 다양성 지표 개선에 기여할 수 있습니다.', '보유 기술이 전략 방향과 일치하여 스킬 역량 공시 점수 상승에 기여할 것으로 예측됩니다.'\n"
        "3) Then a bullet list: '면접/확인 시 질문 또는 가이드'. Give the HR person specific questions or checks to improve disclosure quality (e.g. '면접 시 사내 교육 프로그램 이수 의지를 확인하여 교육 및 개발 지표를 보완할 것을 제안합니다.', '성별·연령대는 입사 후 인사시스템에 반영되므로 채용 후 공시 품질이 향상됩니다.').\n"
        "Do not output only '부적합'. Always provide contribution potential and actionable guide items."
    )
    user_text = (
        f"## ISO 30414 관련 문구\n{context}\n\n## 지원자/직원 데이터\n{employee_summary}\n\n"
        "위 데이터를 바탕으로 (1) 기여 가능/보완 필요 (2) 공시 기여도 예측 요약 (3) 면접·확인 시 질문/가이드 목록을 작성해 주세요."
    )

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
            message=f"기여도 예측 생성 중 오류: {e}",
            suggestions=[],
        )

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    suitable = False
    message_parts: List[str] = []
    suggestions_list: List[str] = []
    for i, line in enumerate(lines):
        if "기여 가능" in line and "보완 필요" not in line:
            suitable = True
        if "보완 필요" in line:
            suitable = False
        is_bullet = line.startswith("-") or line.startswith("•") or line.startswith("*")
        if is_bullet:
            suggestions_list.append(line.lstrip("-•* ").strip())
        elif i > 0 or (i == 0 and "기여 가능" not in line and "보완 필요" not in line):
            if line and len(line) > 5:
                message_parts.append(line)
    message = " ".join(message_parts).strip() if message_parts else (lines[0] if lines else text[:300])
    return DisclosureCheckResponse(
        suitable=suitable,
        message=message or text[:300],
        suggestions=suggestions_list,
    )


@router.get("/status", response_model=DisclosureStatusResponse)
async def get_disclosure_status() -> DisclosureStatusResponse:
    """ISO 30414 문서가 disclosures 테이블에 적재되었는지 조회."""
    db = SessionLocal()
    try:
        count = get_disclosure_doc_count(db)
        return DisclosureStatusResponse(
            ingested=count > 0,
            document_count=count,
        )
    finally:
        db.close()


class DisclosureCheckJobResponse(BaseModel):
    """비동기 공시 확인 요청 즉시 응답."""

    job_id: str = Field(..., description="결과 조회용 작업 ID")


class DisclosureCheckResultResponse(BaseModel):
    """공시 기여도 예측 결과 조회 (폴링)."""

    status: str = Field(..., description="pending | completed | failed")
    result: Optional[DisclosureCheckResponse] = Field(
        None,
        description="완료 시 기여도 예측(suitable, message, suggestions=면접·확인 가이드)",
    )
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
