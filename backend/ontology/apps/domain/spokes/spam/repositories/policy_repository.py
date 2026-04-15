"""
정책 저장소 (PG Vector)

생성이 필요한 동적 정책 데이터를 저장하고 조회합니다.
"""

from typing import Any, Dict, List, Optional


class PolicyRepository:
    """정책 저장소 (PG Vector)."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self._client = None

    def search_policy(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """벡터 검색으로 정책 조회."""
        return []

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """정책 조회."""
        return None

    def generate_policy(self, context: Dict[str, Any], exaone_client: Any) -> str:
        """EXAONE으로 정책 생성."""
        return ""

    def is_policy_based(self, email_metadata: Dict[str, Any]) -> bool:
        """이메일이 정책 기반으로 처리해야 하는지 판단."""
        return True
