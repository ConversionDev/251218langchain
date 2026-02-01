"""
Hub MCP - Llama·ExaOne HTTP 라우터.

역할: Llama Discriminator·ExaOne Solver HTTP 엔드포인트.
spokes가 HTTP로 호출. domain.hub.llm으로 실제 처리.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Hub LLM (Llama + ExaOne)"])


# ---------------------------------------------------------------------------
# Llama
# ---------------------------------------------------------------------------

_llama = APIRouter(prefix="/internal/llama", tags=["Llama Discriminator"])


class ClassifyRequest(BaseModel):
    text: str = Field(..., description="분류할 텍스트")


class ClassifyResponse(BaseModel):
    result: str = Field(..., description="BLOCK | RULE_BASED | POLICY_BASED")


class ClassifySpamRequest(BaseModel):
    email_metadata: dict = Field(..., description="subject, sender, body 등")


class ClassifySpamResponse(BaseModel):
    result: dict = Field(..., description="spam_prob, confidence, label")


@_llama.post("/classify", response_model=ClassifyResponse)
async def llama_classify_endpoint(request: ClassifyRequest) -> ClassifyResponse:
    """시멘틱 분류."""
    try:
        from domain.hub.llm import classify  # type: ignore

        result = classify(request.text.strip()) if request.text else "POLICY_BASED"
        return ClassifyResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_llama.post("/classify_spam", response_model=ClassifySpamResponse)
async def llama_classify_spam_endpoint(request: ClassifySpamRequest) -> ClassifySpamResponse:
    """스팸 분류."""
    try:
        from domain.hub.llm import classify_spam  # type: ignore

        result = classify_spam(request.email_metadata)
        return ClassifySpamResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_llama.get("/health")
async def llama_health():
    return {"status": "ok", "service": "Llama Discriminator"}


# ---------------------------------------------------------------------------
# ExaOne
# ---------------------------------------------------------------------------

_exaone = APIRouter(prefix="/internal/exaone", tags=["ExaOne Solver"])


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="입력 프롬프트")
    max_tokens: int = Field(default=512, description="최대 생성 토큰 수")


class GenerateResponse(BaseModel):
    result: str = Field(..., description="생성된 문자열")


class AnalyzeEmailRequest(BaseModel):
    subject: str = Field(..., description="제목")
    sender: str = Field(..., description="발신자")
    body: str = Field(default="", description="본문")
    recipient: str = Field(default="", description="수신자")
    date: str = Field(default="", description="날짜")
    attachments: Optional[List[str]] = Field(default=None)
    headers: Optional[Dict[str, Any]] = Field(default=None)
    policy_context: str = Field(default="", description="정책 컨텍스트")


class AnalyzeEmailResponse(BaseModel):
    result: Dict[str, Any] = Field(..., description="raw_output, parsed, risk_codes")


@_exaone.post("/generate", response_model=GenerateResponse)
async def exaone_generate_endpoint(request: GenerateRequest) -> GenerateResponse:
    """ExaOne 텍스트 생성."""
    try:
        from domain.hub.llm import generate_text  # type: ignore

        result = generate_text(prompt=request.prompt.strip(), max_tokens=request.max_tokens)
        return GenerateResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_exaone.post("/analyze_email", response_model=AnalyzeEmailResponse)
async def exaone_analyze_email_endpoint(request: AnalyzeEmailRequest) -> AnalyzeEmailResponse:
    """ExaOne 이메일 스팸/위험 분석."""
    try:
        from domain.hub.llm import analyze_email  # type: ignore

        result = analyze_email(
            subject=request.subject,
            sender=request.sender,
            body=request.body or None,
            recipient=request.recipient or None,
            date=request.date or None,
            attachments=request.attachments,
            headers=request.headers,
            policy_context=request.policy_context or None,
        )
        return AnalyzeEmailResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_exaone.get("/health")
async def exaone_health():
    return {"status": "ok", "service": "ExaOne Solver"}


# 통합 라우터 (llama + exaone)
router.include_router(_llama)
router.include_router(_exaone)
