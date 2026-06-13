"""
LLaMA 분류기 (판별기)

역할: 의미 기반 스팸 분류 — 내용(제목·발신자·본문)을 보고 스팸/정상을 구분.
SFT 모델 generate 후 "스팸 확률: 0.xx" 파싱하여 분류.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import torch
from domain.shared.utils import format_email_text  # type: ignore

logger = logging.getLogger(__name__)

# SFT 학습 시 사용한 프롬프트 형식 (finetune.py와 동일)
_SFT_SYSTEM = "당신은 이메일 스팸 분류 전문가입니다. 이메일을 분석하여 스팸 확률을 0.0~1.0 사이 숫자로 답변하세요."
_SPAM_PROB_PATTERN = re.compile(r"스팸\s*확률\s*:\s*([0-9.]+)", re.IGNORECASE)


def _build_sft_prompt(email_text: str) -> str:
    """SFT 학습과 동일한 Llama 3.2 채팅 프롬프트 (generate 입력용)."""
    return (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{_SFT_SYSTEM}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        f"{email_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    )


def _parse_spam_prob_from_output(text: str) -> float:
    """생성된 텍스트에서 '스팸 확률: 0.xx' 파싱. 실패 시 0.5."""
    m = _SPAM_PROB_PATTERN.search(text)
    if not m:
        return 0.5
    try:
        p = float(m.group(1))
        return max(0.0, min(1.0, p))
    except (ValueError, TypeError):
        return 0.5


class LLaMAClassifier:
    """LLaMA SFT 모델 기반 스팸 분류기. 내용을 보고 스팸 확률 생성 후 파싱."""

    def __init__(self, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model: Any = None
        self._tokenizer: Any = None

    def load_model(self) -> None:
        """LlamaManager(베이스+스팸 LoRA) 로드."""
        if self._model is not None:
            return
        from core.resource_manager.llama_manager import get_llama_manager  # type: ignore

        manager = get_llama_manager()
        self._model = manager.get_base_model()
        self._tokenizer = manager.get_tokenizer()
        self._model.eval()

    def predict(
        self, email_metadata: Dict[str, Any], return_confidence: bool = True
    ) -> Dict[str, Any]:
        """스팸 분류 예측. SFT 모델이 내용을 보고 generate 후 '스팸 확률' 파싱."""
        if self._model is None or self._tokenizer is None:
            raise ValueError("먼저 load_model()을 호출하세요.")

        email_text = format_email_text(email_metadata)
        prompt = _build_sft_prompt(email_text)
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            out = self._model.generate(
                **inputs,
                max_new_tokens=24,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        # 입력 길이만큼 자른 뒤 디코딩
        gen = out[0][inputs["input_ids"].shape[1] :]
        decoded = self._tokenizer.decode(gen, skip_special_tokens=False)
        spam_prob = _parse_spam_prob_from_output(decoded)
        if spam_prob == 0.5 and not _SPAM_PROB_PATTERN.search(decoded):
            logger.debug("LLaMA 스팸 파싱 실패(기본 0.5 사용). raw=%r", decoded[:200])

        label = "spam" if spam_prob > 0.5 else "ham"
        confidence = "high"
        if return_confidence:
            distance_from_center = abs(spam_prob - 0.5)
            if distance_from_center < 0.15:
                confidence = "low"
            elif distance_from_center < 0.3:
                confidence = "medium"

        result: Dict[str, Any] = {
            "spam_prob": spam_prob,
            "label": label,
            "model": "llama",
        }
        if return_confidence:
            result["confidence"] = confidence
        return result

    def predict_batch(
        self, email_metadata_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """배치 예측.

        Args:
            email_metadata_list: 이메일 메타데이터 리스트

        Returns:
            분류 결과 리스트
        """
        results = []
        for email_metadata in email_metadata_list:
            result = self.predict(email_metadata)
            results.append(result)
        return results
