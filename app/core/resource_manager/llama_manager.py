"""
LLaMA 스팸 분류 공통 로더 (Hub 싱글톤)

ExaOne과 동일 전략: config(모델 ID·어댑터 사용 여부) + paths(어댑터 디렉터리).
- get_base_model() / get_tokenizer(): 스팸 분류(베이스 + 선택적 LoRA + 분류 헤드)용
"""

from typing import Any, Optional

import threading


def _get_model_id() -> str:
    """설정에서 LLaMA 베이스 모델 ID 반환."""
    from core.config import get_settings  # type: ignore
    return get_settings().llama_model_id


def _get_adapters_dir():
    """스팸 LoRA 어댑터 경로 (설정 켜져 있을 때만 사용)."""
    from core.paths import get_llama_adapters_dir  # type: ignore
    return get_llama_adapters_dir()


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
        """토크나이저 한 번만 로드 후 반환 (설정의 llama_model_id 사용)."""
        if self._tokenizer is None:
            with self._lock:
                if self._tokenizer is None:
                    from transformers import AutoTokenizer

                    model_id = _get_model_id()
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        model_id, trust_remote_code=True
                    )
                    if self._tokenizer.pad_token is None:
                        self._tokenizer.pad_token = self._tokenizer.eos_token
                        self._tokenizer.pad_token_id = self._tokenizer.eos_token_id
        return self._tokenizer

    def get_base_model(self):
        """베이스 CausalLM (4-bit). 설정에 따라 스팸 LoRA 어댑터 로드 (ExaOne competency_adapters와 동일 전략)."""
        if self._base_model is None:
            with self._lock:
                if self._base_model is None:
                    import torch
                    from transformers import AutoModelForCausalLM, BitsAndBytesConfig

                    model_id = _get_model_id()
                    device_map = "cuda:0" if torch.cuda.is_available() else "auto"
                    bnb = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_use_double_quant=True,
                    )
                    self._base_model = AutoModelForCausalLM.from_pretrained(
                        model_id,
                        quantization_config=bnb,
                        device_map=device_map,
                        trust_remote_code=True,
                    )
                    self._base_model.eval()

                    # 스팸 LoRA 어댑터 (설정 켜져 있고 경로 존재 시. ExaOne competency_adapters와 동일 전략)
                    from core.config import get_settings  # type: ignore
                    settings = get_settings()
                    if getattr(settings, "llama_use_spam_adapter", True):
                        adapter_dir = _get_adapters_dir()
                        adapter_config = adapter_dir / "adapter_config.json"
                        if not adapter_config.exists() and (adapter_dir / "final_model").is_dir():
                            adapter_dir = adapter_dir / "final_model"
                            adapter_config = adapter_dir / "adapter_config.json"
                        if adapter_dir.is_dir() and adapter_config.exists():
                            try:
                                from peft import PeftModel  # type: ignore
                                self._base_model = PeftModel.from_pretrained(
                                    self._base_model, str(adapter_dir)
                                )
                                self._base_model.eval()
                                print("[OK] LLaMA 스팸 어댑터 로드 완료 (llama/adapters)")
                            except Exception as e:
                                print(f"[WARN] LLaMA 스팸 어댑터 로드 실패, 베이스만 사용: {e}")
        return self._base_model

    def reset(self) -> None:
        """테스트/리셋용: 캐시 초기화."""
        with self._lock:
            self._base_model = None
            self._tokenizer = None


def get_llama_manager() -> LlamaManager:
    """LlamaManager 싱글톤 인스턴스 반환."""
    return LlamaManager()
