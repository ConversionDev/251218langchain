"""
공통 헬퍼 함수

LangChain LLM 관리를 위한 공통 헬퍼 함수들.
ExaOne은 Hub Adapter 경유, 그 외는 core.llm 사용.
"""

from typing import Any, Optional


def _get_llm_provider():
    """LLMProvider 클래스 반환 (지연 import)."""
    from core.llm.providers.llm_provider import LLMProvider  # type: ignore

    return LLMProvider


def _get_llm(provider: Optional[str] = None, **kwargs):
    """LLM 인스턴스 반환. ExaOne이면 Hub Adapter, 그 외는 core.llm."""
    from core.llm.providers.llm_provider import (  # type: ignore
        LLMProvider,
        get_llm as _core_get_llm,
    )

    effective = provider or LLMProvider.get_provider_name()
    if effective == "exaone":
        from domain.v1.hub.llm import get_llm as _hub_get_llm  # type: ignore
        return _hub_get_llm(**kwargs)
    return _core_get_llm(provider=provider, **kwargs)


def _supports_tool_calling(provider: Optional[str] = None) -> bool:
    """Tool Calling 지원 여부 확인 (지연 import)."""
    from core.llm.providers.llm_provider import supports_tool_calling  # type: ignore

    return supports_tool_calling(provider)
