"""
Domain Models - v1 공통 데이터 규격.

채팅·스팸·이메일 등 도메인 Pydantic 모델 re-export (bases).
※ LangGraph 상태(ChatState/SpamState)는 infrastructure.orchestration.states 로 이동됨.
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

__all__ = [
    "EmailMetadata",
    "EmailRequest",
    "EmailResponse",
    "ExaoneConfig",
    "ExaoneResult",
    "LLaMAResult",
    "SpamResult",
    "VectorSearchQuery",
    "VectorSearchResult",
]
