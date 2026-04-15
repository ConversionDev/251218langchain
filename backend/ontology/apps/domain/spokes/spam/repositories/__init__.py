"""
스팸 도메인 Repository 레이어

데이터 저장소 접근을 담당합니다.
- Rule Repository: Redis 기반 규칙 저장소
- Policy Repository: PG Vector 기반 정책 저장소
"""

from .policy_repository import PolicyRepository
from .rule_repository import RuleRepository

__all__ = ["PolicyRepository", "RuleRepository"]
