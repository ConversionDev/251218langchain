"""
이메일 API 스키마

email_router.py에서 사용하는 Email Request/Response 모델.
스팸 감지 도메인의 API 스키마입니다.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

# 기존 스키마 재사용
from .base_model import EmailMetadata, LLaMAResult  # type: ignore

# EXAONE 결과 모델 import
if TYPE_CHECKING:
    from domain.spam.agents.exaone.models import ExaoneResult  # type: ignore
else:
    from domain.spam.agents.exaone.models import ExaoneResult  # type: ignore


class EmailRequest(BaseModel):
    """이메일 요청 모델.

    email_router.py의 send_mail, spam_mail_filter 엔드포인트에서 사용.
    """

    email_metadata: EmailMetadata = Field(..., description="이메일 메타데이터")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()


class EmailResponse(BaseModel):
    """이메일 처리 응답 모델.

    스팸 필터링 결과를 포함합니다.
    LLaMA와 EXAONE의 분석 결과를 종합하여 최종 결정을 반환합니다.
    """

    action: str = Field(
        ...,
        description="처리 액션 (deliver, deliver_with_warning, quarantine, reject, ask_user_confirm)",
    )
    routing_strategy: Optional[str] = Field(
        None, description="사용된 라우팅 전략 (rule/policy)"
    )
    reason_codes: List[str] = Field(
        default_factory=list, description="이유 코드 리스트"
    )
    user_message: str = Field(..., description="사용자 메시지")
    confidence: str = Field(..., description="신뢰도 (high, medium, low)")
    spam_prob: float = Field(..., description="스팸 확률")
    llama_result: LLaMAResult = Field(..., description="LLaMA 분류 결과")
    exaone_result: Optional[ExaoneResult] = Field(
        default=None, description="EXAONE 분석 결과"
    )
    routing_path: str = Field(..., description="라우팅 경로 (디버깅용)")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()
