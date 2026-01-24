"""
이메일 라우터

이메일 전송 및 스팸 필터링 관련 API 엔드포인트를 제공합니다.
"""

from typing import Any, Dict

from domain.chat.orchestrator import run_spam_detection  # type: ignore
from domain.spam.models.email_model import EmailRequest, EmailResponse  # type: ignore
from fastapi import APIRouter, HTTPException

email_router = APIRouter(prefix="/mail", tags=["mail"])


@email_router.post("/send", response_model=Dict[str, Any])
async def send_mail(email: EmailRequest):
    """이메일 전송 API.

    Args:
        email: 이메일 요청 (메타데이터 포함)

    Returns:
        이메일 전송 결과
    """
    # TODO: 이메일 전송 로직 구현
    # 현재는 스켈레톤만 제공
    return {
        "status": "success",
        "message": "이메일 전송 기능은 아직 구현되지 않았습니다.",
        "email_metadata": email.email_metadata.model_dump(),
    }


@email_router.post("/filter", response_model=EmailResponse)
async def spam_mail_filter(email: EmailRequest):
    """스팸 필터링 API.

    LLaMA 게이트웨이를 통해 빠른 1차 분류를 수행하고,
    애매한 케이스는 EXAONE으로 정밀 분석합니다.

    Args:
        email: 이메일 요청 (메타데이터 포함)

    Returns:
        스팸 필터링 결과
    """
    try:
        # EmailRequest를 딕셔너리로 변환
        email_metadata = email.email_metadata.model_dump()

        # 기존 스팸 감지 로직 재사용
        result = run_spam_detection(email_metadata)

        # run_spam_detection의 반환 형식을 EmailResponse로 변환
        # result에는 final_decision의 내용과 추가 필드들이 포함됨
        routing_path = result.get("routing_path", "")
        routing_strategy = result.get(
            "routing_strategy", "policy"
        )  # 그래프에서 직접 전달받음

        # LLaMA와 EXAONE 결과를 모델로 변환
        from domain.spam.agents.exaone.models import ExaoneResult  # type: ignore
        from domain.spam.models import LLaMAResult  # type: ignore

        llama_result_dict = result.get("llama_result", {})
        exaone_result_dict = result.get("exaone_result")

        llama_result = (
            LLaMAResult(**llama_result_dict)
            if llama_result_dict
            else LLaMAResult(spam_prob=0.5, confidence="low", label="UNCERTAIN")
        )
        exaone_result = (
            ExaoneResult(**exaone_result_dict) if exaone_result_dict else None
        )

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
        raise HTTPException(
            status_code=500,
            detail=f"스팸 필터링 중 오류가 발생했습니다: {str(e)}",
        )
