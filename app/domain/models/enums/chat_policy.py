"""채팅 시멘틱 분류 결과 Enum."""

from enum import Enum


class ChatPolicy(str, Enum):
    """채팅 분류 결과 (Llama 시멘틱 분류)."""

    BLOCK = "BLOCK"
    RULE_BASED = "RULE_BASED"
    POLICY_BASED = "POLICY_BASED"
