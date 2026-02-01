"""
규칙 저장소 (Redis)

생성이 필요없는 정적 규칙 데이터를 저장하고 조회합니다.
"""

from typing import Any, Dict, List, Optional


class RuleRepository:
    """규칙 저장소 (Redis)."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._client = None

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """규칙 조회."""
        return None

    def match_pattern(self, email_metadata: Dict[str, Any]) -> Optional[str]:
        """이메일 메타데이터와 패턴 매칭."""
        return None

    def get_blacklist_senders(self) -> List[str]:
        """블랙리스트 발신자 목록 조회."""
        return []

    def get_keyword_patterns(self) -> List[Dict[str, Any]]:
        """키워드 패턴 목록 조회."""
        return []

    def is_rule_based(self, email_metadata: Dict[str, Any]) -> bool:
        """이메일이 규칙 기반으로 처리 가능한지 판단."""
        return False
