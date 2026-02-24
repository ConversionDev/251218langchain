"""도메인 Enum: 스팸 분류·전략."""

from domain.models.enums.spam_policy import SpamPolicy
from domain.models.enums.strategy_type import StrategyType

__all__ = [
    "SpamPolicy",
    "StrategyType",
]
