"""
오케스트레이션 모델 통합 Export

API 모델과 Agent State 모델을 패키지 레벨에서 export합니다.
스팸 감지 전용 State는 domain/spam/models/state_model.py를 참조하세요.

참고: EmailMetadata는 domain/spam/models/base_model.py에서 통합 관리됩니다.
"""

from .api_models import (
    EmailMetadata,  # spam 도메인에서 re-export
    SpamDetectionRequest,
    SpamDetectionResponse,
)
from .state_models import AgentState

__all__ = [
    # API 모델 (EmailMetadata는 spam 도메인에서 import됨)
    "EmailMetadata",
    "SpamDetectionRequest",
    "SpamDetectionResponse",
    # State 모델
    "AgentState",
    # SpamDetectionState는 domain.spam.models에서 import하세요.
]
