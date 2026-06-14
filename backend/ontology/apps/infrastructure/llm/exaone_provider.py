"""LLM Provider — 텍스트 채팅용 (ExaOne / GGUF).

이미지·멀티모달 응답은 graph에서 gemini_adapter 직접 호출(LLM Provider 아님).

LLM_PROVIDER 환경변수:
  - exaone (기본): GPU 로컬. bitsandbytes NF4 + 역량 어댑터.
  - llama_cpp: CPU 배포. merge+GGUF 단일 파일 + llama-cpp-python.
"""

import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set

from langchain_core.language_models import BaseChatModel

_lock_direct_load = threading.Lock()

_SUPPORTED_PROVIDERS = {"exaone", "llama_cpp", "gemini"}


class LLMProvider:
    """텍스트 채팅 LLM — ExaOne 또는 GGUF(llama.cpp)."""

    _instances: Dict[str, BaseChatModel] = {}
    _creating: Set[str] = set()  # 순환 호출 방지: 생성 중인 cache_key
    _direct_loaded_llm: Optional[BaseChatModel] = None  # _load_exaone_direct()로 한 번만 로드, 재사용
    _supports_tool_calling: Dict[str, bool] = {
        "exaone": True,
        "llama_cpp": True,
        # gemini: 네이티브 function-calling 대신 키워드 강제 도구 라우팅을 쓰지만,
        # model_node의 스트리밍 경로(bind_tools+stream)를 타려면 True여야 한다.
        "gemini": True,
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
            provider: LLM 제공자 (기본: LLM_PROVIDER 환경변수, 없으면 exaone)
            temperature: 생성 온도
            max_tokens: 최대 생성 토큰 수
            **kwargs: 추가 인자

        Returns:
            LangChain 호환 LLM 인스턴스
        """
        provider = provider or cls.get_provider_name()

        cache_key = f"{provider}_{temperature}_{max_tokens}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        if provider not in _SUPPORTED_PROVIDERS:
            raise ValueError(f"지원하지 않는 LLM Provider: {provider}. 가능: {_SUPPORTED_PROVIDERS}")

        if provider == "gemini":
            llm = cls._create_gemini_llm(temperature, max_tokens)
            cls._instances[cache_key] = llm
            return llm

        if provider == "llama_cpp":
            llm = cls._create_llama_cpp_llm(temperature, max_tokens)
            cls._instances[cache_key] = llm
            return llm

        # exaone: 순환 호출 방지
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
    def _create_gemini_llm(cls, temperature: float, max_tokens: int) -> BaseChatModel:
        """Gemini 채팅 모델 (배포 CHAT_LLM=gemini). google.generativeai 스트리밍 래퍼."""
        from core.config import get_settings  # type: ignore
        from infrastructure.llm.gemini_chat import GeminiChatModel  # type: ignore

        settings = get_settings()
        api_key = getattr(settings, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("CHAT_LLM=gemini인데 GEMINI_API_KEY가 없습니다.")
        # 채팅은 flash-lite 권장: thinking 지연이 적어 첫 토큰이 빠르고 무료 티어 한도도 넉넉.
        model_id = (
            getattr(settings, "chat_gemini_model", None)
            or getattr(settings, "gemini_model", None)
            or "gemini-2.5-flash-lite"
        )
        return GeminiChatModel(
            model_id=model_id,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @classmethod
    def _create_llama_cpp_llm(cls, _temperature: float, _max_tokens: int) -> BaseChatModel:
        """GGUF + llama.cpp. exaone_gguf_path / EXAONE_GGUF_PATH / 기본 파일명 순으로 경로 결정."""
        from core.config import get_settings  # type: ignore
        from core.paths import get_output_dir  # type: ignore
        from infrastructure.llm.gguf_exaone_chat import (  # type: ignore
            GgufCompetencyChatModel,
            load_gguf_llama_singleton,
        )

        settings = get_settings()
        path = getattr(settings, "exaone_gguf_path", None) or os.getenv("EXAONE_GGUF_PATH", "").strip()
        if not path:
            path = str(get_output_dir() / "exaone" / "gguf" / "exaone_competency_q4_k_m.gguf")
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(
                f"GGUF 파일이 없습니다: {p.resolve()}\n"
                "scripts/export_exaone_merged_hf_for_gguf.py 실행 후 llama.cpp로 .gguf 변환하고 "
                "artifacts/fine_tuned/exaone/gguf/ 에 두거나 EXAONE_GGUF_PATH 를 설정하세요."
            )
        n_ctx = int(getattr(settings, "exaone_gguf_n_ctx", 8192) or 8192)
        llama = load_gguf_llama_singleton(str(p.resolve()), n_ctx=n_ctx)
        return GgufCompetencyChatModel(llama=llama)

    @classmethod
    def _load_exaone_direct(cls) -> BaseChatModel:
        """ExaOne 모델 직접 로드 (순환 호출 시 사용). 이미 로드된 인스턴스가 있으면 재사용."""
        if cls._direct_loaded_llm is not None:
            return cls._direct_loaded_llm
        with _lock_direct_load:
            if cls._direct_loaded_llm is not None:
                return cls._direct_loaded_llm
            from infrastructure.llm.exaone_hf_model import load_exaone_model  # type: ignore

            exaone_llm = load_exaone_model()
            cls._direct_loaded_llm = exaone_llm.get_langchain_model()
            return cls._direct_loaded_llm

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
        return list(_SUPPORTED_PROVIDERS)

    @classmethod
    def clear_cache(cls) -> None:
        """캐시된 LLM 인스턴스 정리."""
        try:
            from infrastructure.llm.gguf_exaone_chat import reset_gguf_singleton  # type: ignore

            reset_gguf_singleton()
        except Exception:
            pass
        cls._instances.clear()
        cls._direct_loaded_llm = None


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

