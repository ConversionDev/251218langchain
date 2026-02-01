"""이메일 라우터.

이메일 전송 및 스팸 필터링 관련 API 엔드포인트를 제공합니다.
"""

from typing import Any, Dict

from domain.hub.orchestrators import run_spam_detection  # type: ignore
from domain.models import EmailRequest, EmailResponse  # type: ignore
from fastapi import APIRouter, HTTPException

email_router = APIRouter(prefix="/mail", tags=["mail"])


@email_router.post("/send", response_model=Dict[str, Any])
async def send_mail(email: EmailRequest):
    return {
        "status": "success",
        "message": "이메일 전송 기능은 아직 구현되지 않았습니다.",
        "email_metadata": email.email_metadata.model_dump(),
    }


@email_router.post("/filter", response_model=EmailResponse)
async def spam_mail_filter(email: EmailRequest):
    try:
        email_metadata = email.email_metadata.model_dump()
        result = run_spam_detection(email_metadata)
        routing_path = result.get("routing_path", "")
        routing_strategy = result.get("routing_strategy", "policy")
        from domain.models import ExaoneResult  # type: ignore
        from domain.models import LLaMAResult  # type: ignore

        llama_result_dict = result.get("llama_result", {})
        exaone_result_dict = result.get("exaone_result")
        llama_result = (
            LLaMAResult(**llama_result_dict)
            if llama_result_dict
            else LLaMAResult(spam_prob=0.5, confidence="low", label="UNCERTAIN")
        )
        exaone_result = ExaoneResult(**exaone_result_dict) if exaone_result_dict else None

        return EmailResponse(
            action=result.get("action", "ask_user_confirm"),
            routing_strategy=routing_strategy,
            reason_codes=result.get("reason_codes", []),
            user_message=result.get("user_message", "처리 완료"),
            confidence=result.get("confidence", "medium"),
            spam_prob=result.get("spam_prob", 0.5),
            llama_result=llama_result,
            exaone_result=exaone_result,
            routing_path=routing_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스팸 필터링 중 오류가 발생했습니다: {str(e)}")
