"""
API Request/Response 모델 정의

오케스트레이션 계층에서 사용하는 API 계약 모델들.
각 서비스의 결과 모델을 조합하여 최종 응답을 구성합니다.
"""

from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

# 각 서비스의 결과 모델 import (TYPE_CHECKING으로 타입 체커 오류 방지)
# EmailMetadata는 spam 도메인에서 통합 관리
if TYPE_CHECKING:
    from domain.v1.spam.agents.exaone.models import ExaoneResult  # type: ignore
    from domain.v1.spam.models.base_model import EmailMetadata, LLaMAResult  # type: ignore
else:
    from domain.v1.spam.agents.exaone.models import ExaoneResult  # type: ignore
    from domain.v1.spam.models.base_model import EmailMetadata, LLaMAResult  # type: ignore


class SpamDetectionRequest(BaseModel):
    """스팸 감지 요청 모델."""

    email_metadata: EmailMetadata = Field(..., description="이메일 메타데이터")


class SpamDetectionResponse(BaseModel):
    """스팸 감지 응답 모델.

    LLaMA와 EXAONE의 분석 결과를 종합하여 최종 결정을 반환합니다.
    """

    action: str = Field(
        ...,
        description="최종 액션 (deliver, deliver_with_warning, quarantine, reject, ask_user_confirm)",
    )
    reason_codes: List[str] = Field(..., description="이유 코드 리스트")
    user_message: str = Field(..., description="사용자 메시지")
    confidence: str = Field(..., description="신뢰도 (high, medium, low)")
    spam_prob: float = Field(..., description="스팸 확률")
    llama_result: LLaMAResult = Field(..., description="LLaMA 분류 결과")
    exaone_result: Optional[ExaoneResult] = Field(
        default=None, description="EXAONE 분석 결과"
    )
    routing_path: str = Field(..., description="라우팅 경로 (디버깅용)")
