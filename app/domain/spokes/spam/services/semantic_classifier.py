"""
LLaMA 분류기 (판별기)

역할: 빠른 1차 스팸 분류. Hub 공통 Llama 로더(LlamaManager)의 베이스 모델을 사용하며,
last_hidden_state 위에 분류 헤드만 스팸 전용으로 유지합니다.
"""

from typing import Any, Dict, List, Optional

import torch
from domain.hub.shared.utils import format_email_text  # type: ignore
from torch import nn


class LLaMAClassifier:
    """LLaMA 기반 스팸 분류기. Hub LlamaManager 베이스 + 분류 헤드."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        use_finetuned: bool = True,
    ):
        """초기화. model_path/device/use_finetuned는 호환성용으로 받되, 실제 로드는 LlamaManager 사용."""
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model: Any = None
        self._tokenizer: Any = None
        self._classifier_head: Optional[nn.Module] = None

    def load_model(self) -> None:
        """Hub LlamaManager에서 베이스·토크나이저를 받고, 분류 헤드만 부착."""
        if self._model is not None:
            return
        from core.resource_manager.llama_manager import get_llama_manager  # type: ignore

        manager = get_llama_manager()
        base = manager.get_base_model()
        tokenizer = manager.get_tokenizer()
        self._model = base
        self._tokenizer = tokenizer
        hidden_size = base.config.hidden_size
        device = next(base.parameters()).device
        self._classifier_head = nn.Linear(hidden_size, 2).to(device)
        self._model.eval()

    def predict(
        self, email_metadata: Dict[str, Any], return_confidence: bool = True
    ) -> Dict[str, Any]:
        """스팸 분류 예측.

        Args:
            email_metadata: 이메일 메타데이터
            return_confidence: 신뢰도 반환 여부

        Returns:
            분류 결과
                - spam_prob: 스팸 확률 (0.0 ~ 1.0)
                - label: 라벨 ("spam" or "ham")
                - confidence: 신뢰도 ("high", "medium", "low")
        """
        if self._model is None or self._tokenizer is None:
            raise ValueError("먼저 load_model()을 호출하세요.")

        text = format_email_text(email_metadata)
        # max_length: 입력 truncation 전용 (생성 제어는 generate 시 max_new_tokens만 사용)
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, padding=True
        )
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            last_hidden = outputs.last_hidden_state
            cls_embedding = last_hidden[0, 0, :]
            logits = self._classifier_head(cls_embedding.unsqueeze(0))

        # 확률 계산 (이진 분류)
        if logits.shape[1] == 2:
            # [ham, spam] 형태
            probs = torch.softmax(logits, dim=-1)
            spam_prob = probs[0][1].item()  # spam 클래스 확률
        elif logits.shape[1] == 1:
            # 단일 출력인 경우 sigmoid 적용
            spam_prob = torch.sigmoid(logits[0][0]).item()
        else:
            # 예상치 못한 형태 - 기본값 반환
            print(f"[WARNING] 예상치 못한 logits shape: {logits.shape}")
            spam_prob = 0.5  # 중립값

        # 라벨 결정
        label = "spam" if spam_prob > 0.5 else "ham"

        # 신뢰도 계산
        confidence = "high"
        if return_confidence:
            # spam_prob가 0.5에 가까울수록 낮은 신뢰도
            distance_from_center = abs(spam_prob - 0.5)
            if distance_from_center < 0.15:  # 0.35 ~ 0.65
                confidence = "low"
            elif distance_from_center < 0.3:  # 0.2 ~ 0.35 or 0.65 ~ 0.8
                confidence = "medium"
            else:  # 0.0 ~ 0.2 or 0.8 ~ 1.0
                confidence = "high"

        result = {
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
