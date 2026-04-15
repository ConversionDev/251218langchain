"""
Domain Models - v1 공통 데이터 규격.

채팅·스팸·이메일 등 도메인 모델 re-export.
상태(ChatState, SpamState)는 states에서, 나머지는 bases에서.
"""

from domain.models.bases import (  # type: ignore
    EmailMetadata,
    EmailRequest,
    EmailResponse,
    ExaoneConfig,
    ExaoneResult,
    LLaMAResult,
    SpamResult,
    VectorSearchQuery,
    VectorSearchResult,
)
from domain.models.states import ChatState, SpamState  # type: ignore

__all__ = [
    "ChatState",
    "EmailMetadata",
    "EmailRequest",
    "EmailResponse",
    "ExaoneConfig",
    "ExaoneResult",
    "LLaMAResult",
    "SpamState",
    "SpamResult",
    "VectorSearchQuery",
    "VectorSearchResult",
]
