"""
시멘틱 분류 서비스

학습된 Llama 3.2B 어댑터로 사용자 질문을 BLOCK / RULE_BASED / POLICY_BASED 로 분류합니다.
규칙 기반(DB)·정책 기반(LLM)·차단(서비스 밖) 라우팅에 사용합니다.
"""

from pathlib import Path
from typing import Literal, Optional

# app 디렉터리: domain/hub/service -> app
_APP_DIR = Path(__file__).resolve().parent.parent.parent.parent
_ADAPTER_BASE = _APP_DIR / "artifacts" / "semantic_classifier" / "adapters"

# 학습 시 사용한 프롬프트와 동일하게 맞춤
_SYSTEM = (
    "당신은 사용자의 질문이 '규칙 기반(RULE_BASED)' 처리 대상인지, "
    "'정책 기반(POLICY_BASED)' 처리 대상인지, 아니면 '차단(BLOCK)' 대상인지 판단하는 전문가입니다. "
    "질문의 의도와 복잡성을 분석하여 정확한 액션과 그 이유를 답변하세요."
)


def _get_adapter_dir() -> Optional[Path]:
    """어댑터 디렉터리 반환. 루트에 없으면 최신 checkpoint-* 사용."""
    base = _ADAPTER_BASE
    if not base.exists():
        return None
    if (base / "adapter_config.json").exists():
        return base
    checkpoints = [d for d in base.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")]
    if not checkpoints:
        return None
    def _num(p: Path) -> int:
        try:
            return int(p.name.replace("checkpoint-", ""))
        except ValueError:
            return -1
    latest = max(checkpoints, key=_num)
    if (latest / "adapter_config.json").exists():
        return latest
    return None


def _load_model_once():
    """학습된 어댑터 로드 (lazy, 싱글톤)."""
    if _load_model_once._model is not None:
        return _load_model_once._model, _load_model_once._tokenizer

    adapter_dir = _get_adapter_dir()
    if adapter_dir is None:
        return None, None

    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        base_id = "unsloth/Llama-3.2-3B-Instruct"
        device_map = "cuda:0" if torch.cuda.is_available() else "auto"

        try:
            tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir), trust_remote_code=True)
        except Exception:
            tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        base = AutoModelForCausalLM.from_pretrained(
            base_id,
            quantization_config=bnb,
            device_map=device_map,
            trust_remote_code=True,
        )
        model = PeftModel.from_pretrained(base, str(adapter_dir))
        model.eval()

        _load_model_once._model = model
        _load_model_once._tokenizer = tokenizer
        return model, tokenizer
    except Exception:
        _load_model_once._model = None
        _load_model_once._tokenizer = None
        return None, None


_load_model_once._model = None  # type: ignore
_load_model_once._tokenizer = None  # type: ignore


def classify(user_message: str) -> Literal["BLOCK", "RULE_BASED", "POLICY_BASED"]:
    """사용자 메시지를 분류합니다."""
    model, tokenizer = _load_model_once()
    if model is None or tokenizer is None:
        return "POLICY_BASED"

    try:
        import torch

        user_text = (
            f"질문: {user_message.strip()}\n"
            "이 질문은 규칙 기반입니까, 정책 기반입니까, 아니면 차단 대상입니까?"
        )
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_text},
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=64,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        reply = tokenizer.decode(
            out[0][inputs["input_ids"].shape[1] :],
            skip_special_tokens=True,
        ).strip()

        reply_upper = reply.upper()
        if "액션:" in reply or "ACTION:" in reply_upper:
            if "BLOCK" in reply_upper:
                return "BLOCK"
            if "RULE_BASED" in reply_upper or "RULE" in reply_upper:
                return "RULE_BASED"
            if "POLICY_BASED" in reply_upper or "POLICY" in reply_upper:
                return "POLICY_BASED"
        if "BLOCK" in reply_upper:
            return "BLOCK"
        if "RULE_BASED" in reply_upper or "RULE" in reply_upper:
            return "RULE_BASED"
        if "POLICY_BASED" in reply_upper or "POLICY" in reply_upper:
            return "POLICY_BASED"

        return "POLICY_BASED"
    except Exception:
        return "POLICY_BASED"


def is_classifier_available() -> bool:
    """학습된 어댑터가 있어 분류기가 사용 가능한지 여부."""
    return _get_adapter_dir() is not None
