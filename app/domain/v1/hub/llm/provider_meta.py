"""
Provider 메타 정보 - Hub 경유로만 노출.

API·오케스트레이터는 core.llm을 직접 import하지 않고 이 모듈을 사용합니다.
내부적으로 core.llm.providers.llm_provider.LLMProvider에 위임합니다.
"""

from typing import List


def get_provider_name() -> str:
    """현재 설정된 LLM Provider 이름 (예: exaone)."""
    from core.llm.providers.llm_provider import LLMProvider  # type: ignore
    return LLMProvider.get_provider_name()


def list_providers() -> List[str]:
    """지원하는 Provider 목록 (예: ['exaone', 'ollama'])."""
    from core.llm.providers.llm_provider import LLMProvider  # type: ignore
    return LLMProvider.list_providers()


def supports_tool_calling(provider: str | None = None) -> bool:
    """해당 Provider의 Tool Calling 지원 여부."""
    from core.llm.providers.llm_provider import LLMProvider  # type: ignore
    return LLMProvider.supports_tool_calling(provider)
