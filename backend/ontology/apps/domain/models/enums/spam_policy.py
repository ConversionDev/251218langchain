"""스팸 라우팅 전략 Enum (규칙/정책)."""

from enum import Enum


class SpamPolicy(str, Enum):
    """스팸 처리 전략."""

    RULE = "rule"  # 규칙 기반
    POLICY = "policy"  # 정책 기반
