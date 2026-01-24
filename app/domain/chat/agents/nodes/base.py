"""
공통 헬퍼 함수

LangChain LLM 관리를 위한 공통 헬퍼 함수들.
모든 노드에서 공통으로 사용됩니다.
"""

from typing import Any, Optional


def _get_llm_provider():
    """LLMProvider 클래스 반환 (지연 import)."""
    from core.llm.providers.llm_provider import LLMProvider  # type: ignore

    return LLMProvider


def _get_llm(provider: Optional[str] = None, **kwargs):
    """LLM 인스턴스 반환 (지연 import)."""
    from core.llm.providers.llm_provider import get_llm  # type: ignore

    return get_llm(provider=provider, **kwargs)


def _supports_tool_calling(provider: Optional[str] = None) -> bool:
    """Tool Calling 지원 여부 확인 (지연 import)."""
    from core.llm.providers.llm_provider import supports_tool_calling  # type: ignore

    return supports_tool_calling(provider)
