"""도메인 Enum: 스팸 분류·전략·메일 상태."""

from domain.models.enums.mail_enums import AiStatus, MailReceiveStatus
from domain.models.enums.spam_policy import SpamPolicy
from domain.models.enums.strategy_type import StrategyType

__all__ = [
    "AiStatus",
    "MailReceiveStatus",
    "SpamPolicy",
    "StrategyType",
]
