"""LLM Provider - 멀티 모델 지원을 위한 통합 인터페이스.

환경 변수나 설정에 따라 적절한 LLM을 반환합니다.
지원 모델:
- exaone: EXAONE 3.5 (한국어 특화, ReAct 권장)
- ollama: Ollama 로컬 모델 (향후 지원)
"""

import os
from typing import Dict, List, Optional

from langchain_core.language_models import BaseChatModel


class LLMProvider:
    """LLM 제공자 - 멀티 모델 관리."""

    _instances: Dict[str, BaseChatModel] = {}
    _default_provider: Optional[str] = None
    _supports_tool_calling: Dict[str, bool] = {
        "exaone": True,  # EXAONE은 JSON Tool Calling 지원 (프롬프트 기반)
        "ollama": False,  # 대부분 미지원 (모델에 따라 다름)
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
        """LLM 인스턴스 반환.

        Args:
            provider: LLM 제공자 ("exaone", "ollama")
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 인자

        Returns:
            LangChain 호환 LLM 인스턴스
        """
        provider = provider or cls.get_provider_name()

        # 캐시된 인스턴스 반환 (같은 provider면)
        cache_key = f"{provider}_{temperature}_{max_tokens}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        llm: BaseChatModel

        if provider == "exaone":
            llm = cls._create_exaone_llm(temperature, max_tokens, **kwargs)
        elif provider == "ollama":
            llm = cls._create_ollama_llm(temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"지원하지 않는 LLM Provider: {provider}")

        cls._instances[cache_key] = llm
        return llm

    @classmethod
    def _create_exaone_llm(
        cls, temperature: float, max_tokens: int, **kwargs
    ) -> BaseChatModel:
        """EXAONE LLM 생성 (ExaoneManager 싱글톤 사용)."""
        # ExaoneManager를 통해 베이스 모델 싱글톤 사용 (중복 로드 방지)
        from core.resource_manager.exaone_manager import ExaoneManager  # type: ignore

        exaone_manager = ExaoneManager()
        exaone_model = exaone_manager.get_base_model()

        return exaone_model.get_langchain_model()

    @classmethod
    def _create_ollama_llm(
        cls, temperature: float, max_tokens: int, **kwargs
    ) -> BaseChatModel:
        """Ollama LLM 생성 (향후 지원)."""
        try:
            # LangChain 1.x 호환: langchain_community.chat_models 또는 langchain_ollama에서 import 시도
            try:
                from langchain_community.chat_models import ChatOllama
            except ImportError:
                # LangChain 1.x: 별도 패키지로 분리된 경우
                try:
                    from langchain_ollama import ChatOllama
                except ImportError:
                    # 최신 경로 시도
                    from langchain_community.chat_models.ollama import ChatOllama

            model = kwargs.get("model", os.getenv("OLLAMA_MODEL", "llama2"))
            base_url = kwargs.get(
                "base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            )

            return ChatOllama(
                model=model,
                temperature=temperature,
                num_predict=max_tokens,
                base_url=base_url,
            )
        except ImportError:
            raise ImportError(
                "Ollama를 사용하려면 langchain-community를 설치하세요: "
                "pip install langchain-community"
            )

    @classmethod
    def list_providers(cls) -> List[str]:
        """지원하는 Provider 목록 반환."""
        return ["exaone", "ollama"]

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
    """LLM 인스턴스를 반환하는 헬퍼 함수.

    Args:
        provider: LLM 제공자 (None이면 환경 변수 사용)
        temperature: 생성 온도
        max_tokens: 최대 토큰 수
        **kwargs: 추가 인자

    Returns:
        LangChain 호환 LLM 인스턴스
    """
    return LLMProvider.get_llm(provider, temperature, max_tokens, **kwargs)


def supports_tool_calling(provider: Optional[str] = None) -> bool:
    """해당 Provider가 Tool Calling을 지원하는지 확인하는 헬퍼 함수."""
    return LLMProvider.supports_tool_calling(provider)
