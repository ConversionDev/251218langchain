"""
Llama Adapter - Hub의 Llama 진입점.

Llama 모델(시멘틱 분류, 스팸 분류) 접근은 이 어댑터를 통해서만 수행합니다.
내부적으로 domain.hub.llm.llama_classifier(LLaMAGate) 및 hub.service.semantic_classifier를 사용합니다.
"""

from typing import Any, Dict, Literal

# ---------------------------------------------------------------------------
# 시멘틱 분류 (BLOCK / RULE_BASED / POLICY_BASED)
# ---------------------------------------------------------------------------


def classify(text: str) -> Literal["BLOCK", "RULE_BASED", "POLICY_BASED"]:
    """텍스트를 시멘틱 분류합니다.

    Args:
        text: 분류할 텍스트 (채팅 입력 등).

    Returns:
        "BLOCK" | "RULE_BASED" | "POLICY_BASED"
    """
    try:
        from domain.hub.service.semantic_classifier import classify as _classify  # type: ignore

        return _classify(text.strip()) if text else "POLICY_BASED"
    except Exception:
        return "POLICY_BASED"


def is_classifier_available() -> bool:
    """시멘틱 분류기(학습된 어댑터) 사용 가능 여부."""
    try:
        from domain.hub.service.semantic_classifier import is_classifier_available as _available  # type: ignore

        return _available()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 스팸 분류 (이메일 메타데이터 → spam_prob, confidence, label)
# ---------------------------------------------------------------------------

_llama_gate: Any = None


def _get_llama_gate():
    """LLaMAGate 싱글톤 (lazy)."""
    global _llama_gate
    if _llama_gate is None:
        from domain.hub.llm.llama_classifier import LLaMAGate  # type: ignore

        _llama_gate = LLaMAGate()
    return _llama_gate


def classify_spam(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """이메일 메타데이터를 Llama로 스팸 분류합니다.

    Args:
        email_metadata: subject, sender, body 등.

    Returns:
        {"spam_prob": float, "confidence": str, "label": str}
    """
    try:
        gate = _get_llama_gate()
        return gate.classify_spam(email_metadata)
    except Exception:
        return {
            "spam_prob": 0.5,
            "confidence": "low",
            "label": "UNCERTAIN",
        }
