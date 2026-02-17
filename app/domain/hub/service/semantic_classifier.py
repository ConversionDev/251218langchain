"""
시멘틱 분류 서비스

Hub 공통 Llama 로더(LlamaManager)의 베이스+PEFT 어댑터로 사용자 질문을
BLOCK / RULE_BASED / POLICY_BASED 로 분류합니다.
규칙 기반(DB)·정책 기반(LLM)·차단(서비스 밖) 라우팅에 사용합니다.
"""

# 학습 시 사용한 프롬프트와 동일하게 맞춤
_SYSTEM = (
    "당신은 사용자의 질문이 '규칙 기반(RULE_BASED)' 처리 대상인지, "
    "'정책 기반(POLICY_BASED)' 처리 대상인지, 아니면 '차단(BLOCK)' 대상인지 판단하는 전문가입니다. "
    "질문의 의도와 복잡성을 분석하여 정확한 액션과 그 이유를 답변하세요."
)


def classify(user_message: str) -> str:
    """사용자 메시지를 분류합니다. ChatPolicy.*.value 반환."""
    from core.resource_manager.llama_manager import get_llama_manager  # type: ignore
    from domain.models.enums import ChatPolicy  # type: ignore

    manager = get_llama_manager()
    model, tokenizer = manager.get_semantic_model()
    if model is None or tokenizer is None:
        return ChatPolicy.POLICY_BASED.value

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
                return ChatPolicy.BLOCK.value
            if "RULE_BASED" in reply_upper or "RULE" in reply_upper:
                return ChatPolicy.RULE_BASED.value
            if "POLICY_BASED" in reply_upper or "POLICY" in reply_upper:
                return ChatPolicy.POLICY_BASED.value
        if "BLOCK" in reply_upper:
            return ChatPolicy.BLOCK.value
        if "RULE_BASED" in reply_upper or "RULE" in reply_upper:
            return ChatPolicy.RULE_BASED.value
        if "POLICY_BASED" in reply_upper or "POLICY" in reply_upper:
            return ChatPolicy.POLICY_BASED.value

        return ChatPolicy.POLICY_BASED.value
    except Exception:
        return ChatPolicy.POLICY_BASED.value


def is_classifier_available() -> bool:
    """학습된 어댑터가 있어 분류기가 사용 가능한지 여부."""
    from core.resource_manager.llama_manager import get_llama_manager  # type: ignore

    return get_llama_manager().is_semantic_available()
