"""
LLaMA 분류기 (판별기)

역할: 빠른 1차 스팸 분류
- 이메일 메타데이터를 입력받아 spam_prob 계산
- 신뢰도 기반 라우팅을 위한 점수 제공
"""

# 공통 유틸리티 import
from typing import Any, Dict, List, Optional

import torch
from domain.hub.shared.utils import format_email_text  # type: ignore
from transformers import AutoTokenizer

# 로컬 경로 없을 때 사용하는 HF 베이스 모델 (4-bit로 로드)
_DEFAULT_LLAMA_MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"


class LLaMAClassifier:
    """LLaMA 기반 스팸 분류기."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        use_finetuned: bool = True,
    ):
        """초기화.

        Args:
            model_path: HuggingFace 모델 ID (None이면 unsloth/Llama-3.2-3B-Instruct, 캐시에서 4-bit 로드)
            device: 사용할 디바이스 (기본값: "cuda")
            use_finetuned: 미사용 (HF 캐시만 사용)
        """
        if model_path is None:
            model_path = _DEFAULT_LLAMA_MODEL_ID
        self.model_path = model_path
        self.device = device or "cuda"

        # 모델 및 토크나이저
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[Any] = None

    def load_model(self) -> None:
        """모델 및 토크나이저 로드."""
        print("=" * 60)
        print("[INFO] LLaMA 분류기 모델 로딩 시작")
        print("=" * 60)
        print(f"모델 경로: {self.model_path}")
        print(f"디바이스: {self.device}")
        print()

        try:
            # 토크나이저 로드
            print("[Step 1] 토크나이저 로딩 중...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, trust_remote_code=True
            )
            print("[OK] 토크나이저 로딩 완료")
            print()

            # 모델 로드 (HF 캐시 + 4-bit)
            print("[Step 2] 모델 로딩 중...")
            from torch import nn
            from transformers import AutoModel, BitsAndBytesConfig

            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            base_model = AutoModel.from_pretrained(
                self.model_path,
                quantization_config=bnb,
                device_map="cuda:0" if self.device == "cuda" else self.device,
                trust_remote_code=True,
            )
            hidden_size = base_model.config.hidden_size
            base_model.classifier = nn.Linear(hidden_size, 2)
            self.model = base_model
            print("[OK] HuggingFace 캐시 + 4-bit + 분류 헤드 로드됨")
            self.model.eval()

            # 모델 정보 출력
            print(f"[INFO] 모델 타입: {type(self.model).__name__}")
            if hasattr(self.model, "config"):
                print(f"[INFO] 모델 config: {self.model.config}")
            print("[OK] 모델 로딩 완료")
            print()

            print("=" * 60)
            print("[OK] LLaMA 분류기 모델 로딩 완료!")
            print("=" * 60)
            print()

        except Exception as e:
            print(f"[ERROR] 모델 로딩 실패: {e}")
            import traceback

            traceback.print_exc()
            raise

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
        if self.model is None or self.tokenizer is None:
            raise ValueError("먼저 load_model()을 호출하세요.")

        # 이메일 텍스트 변환
        text = format_email_text(email_metadata)

        # 토크나이징
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 예측
        with torch.no_grad():
            outputs = self.model(**inputs)

            # 출력 형태 확인
            if hasattr(outputs, "logits"):
                logits = outputs.logits
            elif hasattr(outputs, "last_hidden_state"):
                # AutoModel인 경우 마지막 hidden state 사용
                last_hidden = outputs.last_hidden_state
                # [CLS] 토큰 사용 (첫 번째 토큰)
                cls_embedding = last_hidden[0, 0, :]  # [batch, seq, hidden] -> [hidden]
                # 분류 헤드가 있으면 사용
                if hasattr(self.model, "classifier"):
                    logits = self.model.classifier(cls_embedding.unsqueeze(0))
                else:
                    # 간단한 선형 변환으로 스팸 확률 추정
                    # (임시 방법 - 실제로는 분류 헤드가 필요)
                    logits = torch.tensor([[0.0, 0.0]])  # 기본값
            else:
                raise ValueError("모델 출력 형식을 확인할 수 없습니다.")

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
