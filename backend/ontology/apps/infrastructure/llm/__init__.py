"""
Infrastructure LLM Adapters — ExaOne / LLaMA / Gemini.

infrastructure.llm의 역할을 이어받은 인프라 어댑터 패키지.
"""

from typing import Any, Dict

from .exaone_adapter import analyze_email, generate_text, get_llm
from .llama_adapter import classify_spam
from .exaone_provider import get_provider_name, list_providers, supports_tool_calling


def classify_spam_by_env(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """SPAM_CLASSIFIER 환경설정에 따라 스팸 1차 분류기 선택 (워커·게이트웨이 공용).

    - gemini: Gemini API (배포 — 무거운 LLaMA 미로드)
    - 그 외(llama): 학습된 LLaMA 어댑터 (로컬/GPU)
    반환 스키마는 동일: {spam_prob, label, confidence, ...}
    """
    from core.config import get_settings  # type: ignore

    if (get_settings().spam_classifier or "llama").lower() == "gemini":
        from .gemini_adapter import gemini_classify_spam  # type: ignore

        return gemini_classify_spam(email_metadata)
    return classify_spam(email_metadata)


__all__ = [
    "classify_spam",
    "classify_spam_by_env",
    "generate_text",
    "get_llm",
    "analyze_email",
    "get_provider_name",
    "list_providers",
    "supports_tool_calling",
]
