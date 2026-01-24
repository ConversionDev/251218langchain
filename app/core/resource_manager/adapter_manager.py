"""
어댑터 관리자

작업별 어댑터의 동적 로딩/언로딩 관리.
"""

import threading
from pathlib import Path
from typing import Any, Dict, Optional

from peft import PeftModel

from .exaone_manager import ExaoneManager


class AdapterManager:
    """어댑터 동적 로딩/언로딩 관리자."""

    _instance: Optional["AdapterManager"] = None
    _lock = threading.Lock()
    _active_adapter_path: Optional[str] = None
    _active_peft_model: Optional[PeftModel] = None

    def __new__(cls):
        """싱글톤 패턴."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def load_adapter(self, adapter_path: Optional[str]) -> Optional[PeftModel]:
        """어댑터 로드.

        Args:
            adapter_path: 어댑터 경로 (None이면 베이스 모델만 사용)

        Returns:
            PEFT 모델 또는 None (베이스 모델만 사용)
        """
        with self._lock:
            # 어댑터 경로가 없으면 베이스 모델만 반환
            if adapter_path is None:
                self._unload_adapter()
                return None

            # 이미 같은 어댑터가 로드되어 있으면 재사용
            if self._active_adapter_path == adapter_path and self._active_peft_model:
                return self._active_peft_model

            # 새 어댑터 로드
            try:
                # 경로 변환
                adapter_path_obj = Path(adapter_path)
                if not adapter_path_obj.is_absolute():
                    # 상대 경로를 절대 경로로 변환
                    project_root = Path(__file__).parent.parent.parent.parent
                    adapter_path_obj = project_root / adapter_path
                    adapter_path = str(adapter_path_obj)

                # EXAONE 베이스 모델 가져오기
                exaone_manager = ExaoneManager()
                base_model = exaone_manager.get_base_model()

                # PEFT 모델 로드
                print(f"[INFO] 어댑터 로딩 중: {adapter_path}")
                peft_model = PeftModel.from_pretrained(
                    base_model.model, adapter_path, device_map="auto"
                )
                print(f"[OK] 어댑터 로딩 완료: {adapter_path}")

                # 기존 어댑터 언로드
                self._unload_adapter()

                # 새 어댑터 저장
                self._active_adapter_path = adapter_path
                self._active_peft_model = peft_model

                return peft_model
            except Exception as e:
                print(f"[WARNING] 어댑터 로딩 실패: {str(e)}")
                return None

    def _unload_adapter(self) -> None:
        """현재 어댑터 언로드."""
        if self._active_peft_model:
            # PEFT 모델 언로드 (메모리 해제)
            self._active_peft_model = None
            self._active_adapter_path = None

    def unload_adapter(self) -> None:
        """어댑터 언로드 (공개 메서드)."""
        with self._lock:
            self._unload_adapter()
