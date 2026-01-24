"""
스팸 도메인 Repository 레이어

데이터 저장소 접근을 담당합니다.
- Rule Repository: Redis 기반 규칙 저장소
- Policy Repository: PG Vector 기반 정책 저장소
"""

from .rule_repository import RuleRepository  # type: ignore
from .policy_repository import PolicyRepository  # type: ignore

__all__ = [
    "RuleRepository",
    "PolicyRepository",
]
