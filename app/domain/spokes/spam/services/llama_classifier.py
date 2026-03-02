"""
LLaMA 분류기 (판별기)

역할: 빠른 1차 스팸 분류.
- 구동 테스트용: 학습 전까지 USE_RULE_FOR_SPAM=True → 키워드 규칙만 사용 (ham → inbox, spam → spam).
- 학습 후: USE_RULE_FOR_SPAM=False 로 바꾸고, 분류 헤드 체크포인트 로드 시 모델 추론 사용.

분류 헤드 출력은 [spam, ham] 순으로 가정 (인덱스 0 = 스팸 확률).
"""

import re
from typing import Any, Dict, List, Optional

import torch
from domain.hub.shared.utils import format_email_text  # type: ignore
from torch import nn

# True: 학습 전 구동 테스트용 — 규칙 기반만 사용. False로 바꾸고 헤드 로드 추가 시 모델 사용.
USE_RULE_FOR_SPAM = True

# 규칙 기반: 아래 키워드가 제목+본문에 있으면 스팸으로 판단 (구동 테스트용)
_SPAM_KEYWORDS = re.compile(
    r"당첨|무료\s*혜택|클릭해|비밀번호\s*입력|한정\s*기간|지금\s*클릭|당첨되셨습니다|광고",
    re.IGNORECASE,
)


def _rule_based_predict(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """학습 전 구동 테스트용. 키워드 규칙으로 spam/ham 판별. ham → inbox, spam → spam."""
    subject = (email_metadata.get("subject") or "")[:500]
    body = (email_metadata.get("body") or "")[:2000]
    text = f"{subject} {body}"
    matches = _SPAM_KEYWORDS.findall(text)
    is_spam = len(matches) >= 1
    spam_prob = 0.85 if is_spam else 0.15
    label = "spam" if is_spam else "ham"
    return {
        "spam_prob": spam_prob,
        "label": label,
        "confidence": "high" if is_spam else "medium",
        "model": "rule",
    }


class LLaMAClassifier:
    """LLaMA 기반 스팸 분류기. USE_RULE_FOR_SPAM=True면 규칙만 사용(구동 테스트), False면 베이스+헤드 사용."""

    def __init__(self, device: Optional[str] = None):
        """초기화. USE_RULE_FOR_SPAM=True면 로드는 하지 않음."""
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model: Any = None
        self._tokenizer: Any = None
        self._classifier_head: Optional[nn.Module] = None
        self._use_rule: bool = False

    def load_model(self) -> None:
        """USE_RULE_FOR_SPAM이면 규칙 모드만 설정. 아니면 Hub LlamaManager + 분류 헤드 로드."""
        if USE_RULE_FOR_SPAM:
            self._use_rule = True
            return
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
        """스팸 분류 예측. 규칙 모드면 키워드만 사용, 아니면 LLaMA+헤드."""
        if getattr(self, "_use_rule", False):
            out = _rule_based_predict(email_metadata)
            if not return_confidence:
                out.pop("confidence", None)
            return out

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

        # 확률 계산 (이진 분류). 헤드 출력 [spam, ham] 순 가정 (인덱스 0 = 스팸).
        if logits.shape[1] == 2:
            probs = torch.softmax(logits, dim=-1)
            spam_prob = probs[0][0].item()  # 스팸 클래스 확률
        elif logits.shape[1] == 1:
            spam_prob = torch.sigmoid(logits[0][0]).item()
        else:
            print(f"[WARNING] 예상치 못한 logits shape: {logits.shape}")
            spam_prob = 0.5

        # 라벨 결정: ham → 받은편지함, spam → 스팸함 (워커에서 folder 매핑)
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
