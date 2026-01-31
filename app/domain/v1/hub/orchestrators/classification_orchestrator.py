"""
분류 오케스트레이터

사용자 메시지를 규칙 기반 / 정책 기반 / 차단(BLOCK)으로 분류하는 진입점입니다.
Hub Llama Adapter를 통해 시멘틱 분류를 호출합니다.
"""

from typing import Literal

from domain.v1.hub.llm import (  # type: ignore
    classify as _classify,
    is_classifier_available as _is_classifier_available,
)


def classify(user_message: str) -> Literal["BLOCK", "RULE_BASED", "POLICY_BASED"]:
    """사용자 메시지를 분류합니다.

    Args:
        user_message: 채팅 입력 문자열.

    Returns:
        "BLOCK" | "RULE_BASED" | "POLICY_BASED"
        - BLOCK: 서비스 범위 밖, 응답 차단
        - RULE_BASED: 규칙/DB로 처리
        - POLICY_BASED: 정책/LLM으로 처리
    """
    return _classify(user_message)


def is_classifier_available() -> bool:
    """학습된 어댑터가 있어 분류기가 사용 가능한지 여부."""
    return _is_classifier_available()


__all__ = ["classify", "is_classifier_available"]
