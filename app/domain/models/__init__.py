"""
Domain Models - v1 공통 데이터 규격.

채팅·스팸·이메일 등 도메인 모델 re-export.
"""

from domain.models.bases import (  # type: ignore
    AgentState,
    EmailMetadata,
    EmailRequest,
    EmailResponse,
    ExaoneConfig,
    ExaoneResult,
    LLaMAResult,
    SpamDetectionState,
    SpamResult,
    VectorSearchQuery,
    VectorSearchResult,
)

__all__ = [
    "AgentState",
    "EmailMetadata",
    "EmailRequest",
    "EmailResponse",
    "ExaoneConfig",
    "ExaoneResult",
    "LLaMAResult",
    "SpamDetectionState",
    "SpamResult",
    "VectorSearchQuery",
    "VectorSearchResult",
]
