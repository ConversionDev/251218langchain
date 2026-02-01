"""LLM Provider - ExaOne 통합 인터페이스.

환경 변수나 설정에 따라 ExaOne LLM을 반환합니다.
역할: Hub Adapter(domain.hub.llm)의 백엔드.
"""

import os
from typing import Dict, List, Optional, Set

from langchain_core.language_models import BaseChatModel


class LLMProvider:
    """LLM 제공자 - ExaOne 관리."""

    _instances: Dict[str, BaseChatModel] = {}
    _creating: Set[str] = set()  # 순환 호출 방지: 생성 중인 cache_key
    _supports_tool_calling: Dict[str, bool] = {
        "exaone": True,  # EXAONE은 JSON Tool Calling 지원 (프롬프트 기반)
    }

    @classmethod
    def get_provider_name(cls) -> str:
        """현재 설정된 LLM Provider 이름 반환."""
        return os.getenv("LLM_PROVIDER", "exaone").lower()

    @classmethod
    def supports_tool_calling(cls, provider: Optional[str] = None) -> bool:
        """해당 Provider가 Tool Calling을 지원하는지 확인."""
        provider = provider or cls.get_provider_name()
        return cls._supports_tool_calling.get(provider, False)

    @classmethod
    def get_llm(
        cls,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> BaseChatModel:
        """LLM 인스턴스 반환 (ExaOne).

        Args:
            provider: LLM 제공자 (기본: exaone)
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 인자

        Returns:
            LangChain 호환 LLM 인스턴스
        """
        provider = provider or cls.get_provider_name()

        cache_key = f"{provider}_{temperature}_{max_tokens}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        if provider != "exaone":
            raise ValueError(f"지원하지 않는 LLM Provider: {provider}")

        # 순환 호출: ExaoneManager -> wrapper.get_langchain_model() -> get_llm() 재진입 시 직접 로드
        if cache_key in cls._creating:
            llm = cls._load_exaone_direct()
            cls._instances[cache_key] = llm
            cls._creating.discard(cache_key)
            return llm

        cls._creating.add(cache_key)
        try:
            llm = cls._create_exaone_llm(temperature, max_tokens, **kwargs)
            cls._instances[cache_key] = llm
            return llm
        finally:
            cls._creating.discard(cache_key)

    @classmethod
    def _load_exaone_direct(cls) -> BaseChatModel:
        """ExaOne 모델 직접 로드 (순환 호출 시 사용). domain.models.bases.exaone_model 사용."""
        from domain.models.bases.exaone_model import load_exaone_model  # type: ignore

        exaone_llm = load_exaone_model(register=False)
        return exaone_llm.get_langchain_model()

    @classmethod
    def _create_exaone_llm(
        cls, temperature: float, max_tokens: int, **kwargs
    ) -> BaseChatModel:
        """EXAONE LLM 생성 (ExaoneManager 싱글톤 사용)."""
        from core.resource_manager.exaone_manager import ExaoneManager  # type: ignore

        exaone_manager = ExaoneManager()
        exaone_model = exaone_manager.get_base_model()
        return exaone_model.get_langchain_model()

    @classmethod
    def list_providers(cls) -> List[str]:
        """지원하는 Provider 목록 반환."""
        return ["exaone"]

    @classmethod
    def clear_cache(cls) -> None:
        """캐시된 LLM 인스턴스 정리."""
        cls._instances.clear()


def get_llm(
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> BaseChatModel:
    """LLM 인스턴스를 반환하는 헬퍼 함수."""
    return LLMProvider.get_llm(provider, temperature, max_tokens, **kwargs)


def get_provider_name() -> str:
    """현재 설정된 LLM Provider 이름 (예: exaone)."""
    return LLMProvider.get_provider_name()


def list_providers() -> List[str]:
    """지원하는 Provider 목록 (예: ['exaone'])."""
    return LLMProvider.list_providers()


def supports_tool_calling(provider: Optional[str] = None) -> bool:
    """해당 Provider가 Tool Calling을 지원하는지 확인하는 헬퍼 함수."""
    return LLMProvider.supports_tool_calling(provider)

