"""
EXAONE 관리자

EXAONE 베이스 모델의 싱글톤 관리.
"""

import threading
from typing import Any, Optional

from core.llm.providers.exaone.exaone_model import ExaoneLLM  # type: ignore


class ExaoneManager:
    """EXAONE 베이스 모델 싱글톤 관리자."""

    _instance: Optional["ExaoneManager"] = None
    _lock = threading.Lock()
    _base_model: Optional[ExaoneLLM] = None

    def __new__(cls):
        """싱글톤 패턴."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_base_model(self) -> ExaoneLLM:
        """EXAONE 베이스 모델 인스턴스 반환 (싱글톤).

        Returns:
            EXAONE 베이스 모델
        """
        if self._base_model is None:
            with self._lock:
                if self._base_model is None:
                    print("[INFO] EXAONE 베이스 모델 로딩 중...")
                    # 환경 변수에서 모델 경로 확인 (ExaoneLLM이 처리)
                    self._base_model = ExaoneLLM(
                        model_path=None,  # EXAONE_MODEL_DIR 환경 변수 사용
                        device_map="auto",
                        use_4bit=True,  # VRAM 절약
                    )
                    print("[OK] EXAONE 베이스 모델 로딩 완료")
        return self._base_model

    def reset(self) -> None:
        """베이스 모델 리셋 (테스트용)."""
        with self._lock:
            self._base_model = None
