"""
[Domain Model] v1 공통 데이터 규격 (bases)

스팸·채팅 등 v1 도메인의 데이터 모델 및 스키마 정의.
상태(ChatState, SpamState)는 domain.models.states 에서 관리.
"""

from .spam_model import EmailMetadata, LLaMAResult, SpamResult
from .email_model import EmailRequest, EmailResponse
from .vector_model import VectorSearchQuery, VectorSearchResult
from .exaone_result_model import ExaoneResult, ExaoneConfig

__all__ = [
    "EmailMetadata",
    "LLaMAResult",
    "SpamResult",
    "EmailRequest",
    "EmailResponse",
    "VectorSearchQuery",
    "VectorSearchResult",
    "ExaoneResult",
    "ExaoneConfig",
]
