"""
EXAONE 관리자

EXAONE 베이스 모델의 싱글톤 관리. domain.hub.llm(ExaOne Provider)을 사용합니다.
"""

import threading
from typing import Any, Optional


class _ExaoneWrapper:
    """ExaOne LLM 래퍼 — invoke / get_langchain_model API 유지."""

    def __init__(self) -> None:
        self._llm: Any = None

    def _get_llm(self) -> Any:
        if self._llm is None:
            from infrastructure.llm.exaone_provider import get_llm, get_provider_name  # type: ignore

            self._llm = get_llm(
                provider=get_provider_name(),
                temperature=0.3,
                max_tokens=2048,
            )
        return self._llm

    def invoke(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.3,
    ) -> str:
        """프롬프트로 텍스트 생성. 생성 길이 제어는 max_new_tokens만 사용 (HF 권장)."""
        from langchain_core.messages import HumanMessage  # type: ignore

        llm = self._get_llm()
        messages = [HumanMessage(content=prompt)]
        out = llm.invoke(messages)
        content = getattr(out, "content", None) or str(out)
        return content if isinstance(content, str) else str(content)

    def get_langchain_model(self) -> Any:
        """LangChain 호환 LLM 반환."""
        return self._get_llm()


class ExaoneManager:
    """EXAONE 베이스 모델 싱글톤 관리자."""

    _instance: Optional["ExaoneManager"] = None
    _lock = threading.Lock()
    _base_model: Optional[_ExaoneWrapper] = None

    def __new__(cls):
        """싱글톤 패턴."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_base_model(self) -> _ExaoneWrapper:
        """EXAONE 베이스 모델 인스턴스 반환 (싱글톤)."""
        if self._base_model is None:
            with self._lock:
                if self._base_model is None:
                    print("[INFO] EXAONE 베이스 모델 로딩 중...")
                    self._base_model = _ExaoneWrapper()
                    print("[OK] EXAONE 베이스 모델 로딩 완료")
        return self._base_model

    def reset(self) -> None:
        """베이스 모델 리셋 (테스트용)."""
        with self._lock:
            self._base_model = None
