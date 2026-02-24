"""
Llama 3.2B 공통 로더 (Hub 싱글톤)

스팸 분류가 동일 프로세스에서 같은 베이스 모델을 한 번만 로드하도록 관리합니다.
- get_base_model() / get_tokenizer(): 스팸 분류(베이스 + 분류 헤드)용
"""

from pathlib import Path
from typing import Any, Optional

import threading

_BASE_LLAMA_ID = "unsloth/Llama-3.2-3B-Instruct"


class LlamaManager:
    """Llama 3.2B 베이스·토크나이저 싱글톤 (스팸 분류용)."""

    _instance: Optional["LlamaManager"] = None
    _lock = threading.Lock()
    _base_model: Any = None
    _tokenizer: Any = None

    def __new__(cls) -> "LlamaManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_tokenizer(self):
        """토크나이저 한 번만 로드 후 반환."""
        if self._tokenizer is None:
            with self._lock:
                if self._tokenizer is None:
                    from transformers import AutoTokenizer

                    self._tokenizer = AutoTokenizer.from_pretrained(
                        _BASE_LLAMA_ID, trust_remote_code=True
                    )
                    if self._tokenizer.pad_token is None:
                        self._tokenizer.pad_token = self._tokenizer.eos_token
                        self._tokenizer.pad_token_id = self._tokenizer.eos_token_id
        return self._tokenizer

    def get_base_model(self):
        """베이스 CausalLM (4-bit). 스팸 분류 등에서 last_hidden_state + 헤드용."""
        if self._base_model is None:
            with self._lock:
                if self._base_model is None:
                    import torch
                    from transformers import AutoModelForCausalLM, BitsAndBytesConfig

                    device_map = "cuda:0" if torch.cuda.is_available() else "auto"
                    bnb = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_use_double_quant=True,
                    )
                    self._base_model = AutoModelForCausalLM.from_pretrained(
                        _BASE_LLAMA_ID,
                        quantization_config=bnb,
                        device_map=device_map,
                        trust_remote_code=True,
                    )
                    self._base_model.eval()
        return self._base_model

    def reset(self) -> None:
        """테스트/리셋용: 캐시 초기화."""
        with self._lock:
            self._base_model = None
            self._tokenizer = None


def get_llama_manager() -> LlamaManager:
    """LlamaManager 싱글톤 인스턴스 반환."""
    return LlamaManager()
