"""공시(ISO 30414) 유스케이스 — 기여도 예측, 임베딩."""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from infrastructure.persistence.repositories.disclosure_repository import (  # type: ignore
    fill_embeddings_for_disclosures,
    get_disclosure_doc_count,
    get_disclosure_embedded_count,
    search_disclosures,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ DTOs

class DisclosureCheckRequest(BaseModel):
    name: str = Field("", description="이름")
    job_title: str = Field("", description="직급")
    department: str = Field("", description="부서")
    email: Optional[str] = Field(None, description="이메일")
    gender: Optional[str] = Field(None, description="성별")
    age: Optional[int] = Field(None, description="연령(만 나이)")
    age_band: Optional[str] = Field(None, description="연령대")
    employment_type: Optional[str] = Field(None, description="고용 형태")
    training_hours: Optional[int] = Field(None, description="연간 교육시간")


class DisclosureCheckResponse(BaseModel):
    suitable: bool
    message: str
    suggestions: List[str] = Field(default_factory=list)


class DisclosureStatusResponse(BaseModel):
    ingested: bool
    document_count: int
    embedded_count: int = 0
    embedding_ratio: float = 0.0


class EmbeddingRunResponse(BaseModel):
    success: bool
    processed: int = 0
    total: int = 0
    embedded: int = 0
    message: str = ""


# ------------------------------------------------------------------ Service

class DisclosureService:

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_status(self) -> DisclosureStatusResponse:
        total = get_disclosure_doc_count(self.db)
        embedded = get_disclosure_embedded_count(self.db)
        ratio = (embedded / total) if total > 0 else 0.0
        return DisclosureStatusResponse(
            ingested=total > 0,
            document_count=total,
            embedded_count=embedded,
            embedding_ratio=round(ratio, 4),
        )

    def run_check(self, payload: DisclosureCheckRequest) -> DisclosureCheckResponse:
        """RAG(disclosures) + LLM으로 공시 기여도 예측."""
        count = get_disclosure_doc_count(self.db)
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
        if payload.age is not None:
            employee_summary += f" 연령 {payload.age}세."
        elif payload.age_band:
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
            contents = search_disclosures(self.db, query_vec, k=5)
            context = "\n\n".join(c[:1500] for c in contents)
        except Exception as e:
            logger.exception("Disclosure 검색 실패: %s", e)
            return DisclosureCheckResponse(
                suitable=False,
                message=f"공시 문서 검색 중 오류: {e}",
                suggestions=[],
            )

        from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
        from infrastructure.llm import get_llm  # type: ignore

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
            text = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.exception("LLM 호출 실패: %s", e)
            return DisclosureCheckResponse(
                suitable=False,
                message=f"기여도 예측 생성 중 오류: {e}",
                suggestions=[],
            )

        return self._parse_llm_response(text)

    def _parse_llm_response(self, text: str) -> DisclosureCheckResponse:
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        suitable = False
        message_parts: List[str] = []
        suggestions: List[str] = []
        for i, line in enumerate(lines):
            if "기여 가능" in line and "보완 필요" not in line:
                suitable = True
            if "보완 필요" in line:
                suitable = False
            is_bullet = line.startswith("-") or line.startswith("•") or line.startswith("*")
            if is_bullet:
                suggestions.append(line.lstrip("-•* ").strip())
            elif i > 0 or (i == 0 and "기여 가능" not in line and "보완 필요" not in line):
                if line and len(line) > 5:
                    message_parts.append(line)
        message = " ".join(message_parts).strip() if message_parts else (lines[0] if lines else text[:300])
        return DisclosureCheckResponse(
            suitable=suitable,
            message=message or text[:300],
            suggestions=suggestions,
        )

    def run_embedding(self) -> EmbeddingRunResponse:
        """embedding이 null인 공시 문서에 임베딩을 채운다."""
        try:
            from domain.shared.embedding import get_disclosure_embedding_model  # type: ignore
            emb_model = get_disclosure_embedding_model()
            if emb_model is None:
                return EmbeddingRunResponse(success=False, message="임베딩 모델을 로드할 수 없습니다.")
            processed = fill_embeddings_for_disclosures(self.db, emb_model)
            self.db.commit()
            total = get_disclosure_doc_count(self.db)
            embedded = get_disclosure_embedded_count(self.db)
            return EmbeddingRunResponse(
                success=True,
                processed=processed,
                total=total,
                embedded=embedded,
                message=f"임베딩 완료: {processed}건 처리됨 ({embedded}/{total})",
            )
        except Exception as e:
            logger.exception("임베딩 실행 실패: %s", e)
            self.db.rollback()
            return EmbeddingRunResponse(success=False, message=f"실패: {str(e)}")
