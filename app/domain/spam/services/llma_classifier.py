"""
LLaMA 분류기 (판별기)

역할: 빠른 1차 스팸 분류
- 이메일 메타데이터를 입력받아 spam_prob 계산
- 신뢰도 기반 라우팅을 위한 점수 제공
"""

# 공통 유틸리티 import
from typing import Any, Dict, List, Optional

import torch
from domain.spam.services.utils import format_email_text  # type: ignore
from transformers import AutoModelForSequenceClassification, AutoTokenizer


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
            model_path: LLaMA 모델 경로 (None이면 app/artifacts 경로에서 탐색)
            device: 사용할 디바이스 (기본값: "cuda", GPU 필수)
            use_finetuned: Fine-tuning된 모델 우선 사용 여부
        """
        # 모델 경로 탐색 (app/artifacts 경로 사용)
        if model_path is None:
            # Fine-tuning된 모델 우선 확인
            if use_finetuned:
                from domain.spam.services.utils import (
                    get_fine_tuned_dir,  # type: ignore
                )

                finetuned_dir = (
                    get_fine_tuned_dir() / "llama" / "adapters" / "final_model"
                )
                if finetuned_dir.exists() and (finetuned_dir / "config.json").exists():
                    model_path = str(finetuned_dir)
                    print(f"[INFO] Fine-tuning된 모델 사용: {model_path}")
                else:
                    print(
                        "[WARNING] Fine-tuning된 모델을 찾을 수 없습니다. Base 모델을 사용합니다."
                    )
                    print("[INFO] Fine-tuning을 실행하려면: python finetune_llama.py")

            # Fine-tuning된 모델이 없으면 base 모델 사용
            if model_path is None:
                from domain.spam.services.utils import (
                    get_base_models_dir,  # type: ignore
                )

                base_models_dir = get_base_models_dir()
                llama_dir = base_models_dir / "llama"
                if llama_dir.exists() and (llama_dir / "config.json").exists():
                    model_path = str(llama_dir)
                else:
                    raise ValueError(
                        "LLaMA 모델 경로를 찾을 수 없습니다. "
                        "app/artifacts/base_models/llama 디렉토리를 확인하세요."
                    )

        self.model_path = model_path
        self.device = device or "cuda"

        # 모델 및 토크나이저
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSequenceClassification] = None

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

            # 모델 로드
            print("[Step 2] 모델 로딩 중...")
            try:
                # 먼저 SequenceClassification으로 시도
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_path,
                    num_labels=2,  # 이진 분류 (ham, spam)
                    trust_remote_code=True,
                )
                print("[OK] AutoModelForSequenceClassification로 로드됨")
            except Exception as e1:
                print(f"[WARNING] SequenceClassification 로드 실패: {e1}")
                print("[INFO] AutoModel로 시도 중...")
                try:
                    from transformers import AutoModel

                    base_model = AutoModel.from_pretrained(
                        self.model_path,
                        trust_remote_code=True,
                    )
                    # 분류 헤드 추가
                    from torch import nn

                    num_labels = 2  # 이진 분류
                    hidden_size = base_model.config.hidden_size
                    classifier = nn.Linear(hidden_size, num_labels)
                    # 모델에 분류 헤드 추가
                    base_model.classifier = classifier
                    self.model = base_model
                    print("[OK] AutoModel + 분류 헤드 추가로 로드됨")
                    print(
                        "[WARNING] 이 모델은 fine-tuning되지 않았습니다. 성능이 제한적일 수 있습니다."
                    )
                    print("[INFO] Fine-tuning을 실행하려면: python finetune_llama.py")
                except Exception as e2:
                    print(f"[ERROR] 모델 로드 실패: {e2}")
                    raise

            self.model.to(self.device)
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
