"""
Classification Orchestrator — 시멘틱 분류 진입점

- 규칙/정책 관련 질문일 때만 시멘틱 분류(BLOCK / RULE_BASED / POLICY_BASED) 수행.
- 그 외(일반 질문)는 분류 없이 Chat 경로만 사용(일반 ExaOne).
"""

from typing import Literal

from domain.hub.llm import (  # type: ignore
    classify as _classify,
    is_classifier_available as _is_classifier_available,
)

# 규칙/정책 관련 키워드: 이 중 하나라도 있으면 시멘틱 분류 수행
_RULE_POLICY_KEYWORDS = (
    "규칙", "정책", "규정", "정책 기반", "규칙 기반", "차단",
    "rule", "policy", "block", "RULE_BASED", "POLICY_BASED", "BLOCK",
)


def is_rule_policy_related(user_message: str) -> bool:
    """질문이 규칙/정책 관련인지 여부. True면 시멘틱 분류 수행, False면 일반 ExaOne(Chat)만 사용."""
    if not user_message or not user_message.strip():
        return False
    lower = user_message.strip().lower()
    return any(kw.lower() in lower for kw in _RULE_POLICY_KEYWORDS)


def classify(user_message: str) -> Literal["BLOCK", "RULE_BASED", "POLICY_BASED"]:
    """사용자 메시지를 시멘틱 분류합니다. 규칙/정책 관련 질문에만 호출 권장.

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


__all__ = ["classify", "is_classifier_available", "is_rule_policy_related"]
