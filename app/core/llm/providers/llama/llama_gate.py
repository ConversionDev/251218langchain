"""LLaMA Gate - 요청 분류를 위한 경량 래퍼.

LLaMA 3.2 3B를 사용하여 규칙 기반/정책 기반 요청을 분류합니다.
Unsloth를 사용하여 추론 속도를 최적화합니다.

성능:
    - 속도: 기존 대비 2배 향상
    - 메모리: 60-80% 절약 (4bit 양자화)
    - XFormers 없이도 Unsloth 자체 최적화로 충분한 성능
"""

import os
import sys

# ============================================================================
# Windows 환경 설정 (최적화)
# ============================================================================

# OpenMP 충돌 방지
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

# TorchInductor/Triton 비활성화 (Windows 안정성)
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHINDUCTOR_DISABLE"] = "1"

# 토크나이저 병렬화 비활성화
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# ============================================================================
# XFormers/FlashAttention 정상 import (Mock 제거)
# ============================================================================
# xformers와 flash_attn이 설치되어 있으면 정상적으로 사용
# 설치되어 있지 않으면 Unsloth가 자체 최적화를 사용
try:
    import xformers  # noqa: F401, type: ignore
    print("[INFO] xformers 정상 로드 완료")
except ImportError:
    print("[INFO] xformers가 설치되지 않았습니다. Unsloth 자체 최적화를 사용합니다.")

try:
    import flash_attn  # noqa: F401, type: ignore
    print("[INFO] flash_attn 정상 로드 완료")
except ImportError:
    print("[INFO] flash_attn이 설치되지 않았습니다. Unsloth 자체 최적화를 사용합니다.")

# ============================================================================
# Unsloth 및 PyTorch Import
# ============================================================================
import torch  # noqa: E402
import unsloth  # noqa: E402, F401
from unsloth import FastLanguageModel  # noqa: E402


class LLaMAGate:
    """LLaMA Gate - 요청 분류용 경량 래퍼 (Unsloth 최적화)."""

    def __init__(
        self,
        model_id: str = "unsloth/Llama-3.2-3B-Instruct",
        max_seq_length: int = 512,
        load_in_4bit: bool = True,
    ):
        """LLaMA Gate 초기화.

        Args:
            model_id: HuggingFace 모델 ID (unsloth 최적화 모델 권장)
            max_seq_length: 최대 시퀀스 길이
            load_in_4bit: 4-bit 양자화 사용 여부
        """
        self.model_id = model_id
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None
        
        # GPU 필수 확인
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA가 사용 불가능합니다. GPU가 필요합니다.\n"
                "torch.cuda.is_available()이 False입니다."
            )
        
        self.device = "cuda"
        self._load_model()

    def _load_model(self) -> None:
        """Unsloth를 사용하여 LLaMA 모델 로드."""
        try:
            print(f"[INFO] LLaMA Gate (Unsloth) 모델 로딩 중: {self.model_id}")

            # 양자화 필수 확인
            if self.load_in_4bit:
                # bitsandbytes 필수 확인
                try:
                    import bitsandbytes  # noqa: F401

                    print("[INFO] bitsandbytes 확인 완료 - 4bit 양자화 사용")
                except ImportError:
                    raise ImportError(
                        "4bit 양자화를 사용하려면 bitsandbytes가 필요합니다. "
                        "설치: pip install bitsandbytes"
                    )

                # CUDA는 이미 초기화 시 확인됨 (GPU 전용)

            # Unsloth FastLanguageModel로 로드
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_id,
                max_seq_length=self.max_seq_length,
                dtype=None,  # 자동 감지
                load_in_4bit=self.load_in_4bit,
            )

            # 양자화 적용 확인
            if self.load_in_4bit:
                # 모델이 양자화되었는지 확인
                try:
                    # Unsloth는 양자화된 모델을 특별한 타입으로 래핑
                    model_type = str(type(self.model))
                    model_dtype = next(self.model.parameters()).dtype

                    # 양자화 확인: bitsandbytes의 Linear4bit 또는 8bit 레이어 확인
                    has_quantized = False
                    for name, module in self.model.named_modules():
                        if "Linear4bit" in str(type(module)) or "Linear8bit" in str(
                            type(module)
                        ):
                            has_quantized = True
                            break

                    if has_quantized:
                        print("[OK] 4bit 양자화가 성공적으로 적용되었습니다.")
                    else:
                        print(
                            f"[WARNING] 양자화 레이어를 찾을 수 없습니다. "
                            f"모델 타입: {model_type}, dtype: {model_dtype}"
                        )
                except Exception as e:
                    print(f"[WARNING] 양자화 확인 중 오류: {e} (계속 진행합니다)")

            # 추론 모드로 최적화
            FastLanguageModel.for_inference(self.model)

            # pad_token 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            print("[OK] LLaMA Gate (Unsloth) 모델 로딩 완료")
        except Exception as e:
            print(f"[ERROR] LLaMA Gate 모델 로딩 실패: {e}")
            raise

    def classify(
        self,
        text: str,
        threshold: float = 0.5,
    ) -> str:
        """요청 타입 분류 (규칙 기반 vs 정책 기반).

        Args:
            text: 분류할 텍스트
            threshold: 정책 기반 판단 임계값 (0.0~1.0)

        Returns:
            "rule_based" 또는 "policy_based"
        """
        if self.model is None or self.tokenizer is None:
            return "policy_based"

        try:
            # 분류 프롬프트
            prompt = f"""다음 요청을 분석하여 규칙 기반 처리인지 정책 기반 처리인지 판단하세요.

요청 내용: {text}

규칙 기반 처리: 명확한 규칙이나 표준 절차로 처리 가능한 경우
정책 기반 처리: 복잡한 판단이나 해석이 필요한 경우

응답은 반드시 다음 중 하나로만 답변하세요:
- "rule_based"
- "policy_based"
"""

            # 토크나이징
            messages = [{"role": "user", "content": prompt}]
            # apply_chat_template은 리스트를 반환할 수 있음
            formatted = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self.tokenizer(
                formatted,
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            # 디코딩 (입력 길이 이후 부분만)
            input_length = inputs["input_ids"].shape[1]
            response = (
                self.tokenizer.decode(
                    outputs[0][input_length:], skip_special_tokens=True
                )
                .strip()
                .lower()
            )

            # 응답 파싱
            if "policy_based" in response or "policy" in response:
                return "policy_based"
            elif "rule_based" in response or "rule" in response:
                return "rule_based"
            else:
                # 기본값: 정책 기반
                return "policy_based"

        except Exception as e:
            print(f"[WARNING] LLaMA Gate 분류 실패, 기본값(정책 기반) 사용: {e}")
            return "policy_based"

    def classify_spam(self, email_data: dict) -> dict:
        """이메일 스팸 분류.

        Args:
            email_data: 이메일 메타데이터
                - subject: 제목
                - sender: 발신자
                - body: 본문

        Returns:
            스팸 분류 결과
            {
                "spam_prob": float (0.0~1.0),
                "confidence": str ("high", "medium", "low"),
                "label": str ("SPAM", "HAM", "UNCERTAIN"),
            }
        """
        if self.model is None or self.tokenizer is None:
            return {
                "spam_prob": 0.5,
                "confidence": "low",
                "label": "UNCERTAIN",
            }

        try:
            subject = email_data.get("subject", "")
            sender = email_data.get("sender", "")
            body = email_data.get("body", "")[:500]  # 본문 500자 제한

            prompt = f"""다음 이메일을 분석하여 스팸 여부를 판단하세요.

제목: {subject}
발신자: {sender}
본문: {body}

스팸 확률을 0.0~1.0 사이 숫자로 답변하세요.
- 0.0~0.3: 정상 메일 (HAM)
- 0.3~0.7: 불확실 (UNCERTAIN)
- 0.7~1.0: 스팸 (SPAM)

응답 형식: 숫자만 (예: 0.85)
"""

            messages = [{"role": "user", "content": prompt}]
            formatted = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self.tokenizer(
                formatted,
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            input_length = inputs["input_ids"].shape[1]
            response = self.tokenizer.decode(
                outputs[0][input_length:], skip_special_tokens=True
            ).strip()

            # 숫자 파싱
            import re

            match = re.search(r"(\d+\.?\d*)", response)
            if match:
                spam_prob = float(match.group(1))
                spam_prob = max(0.0, min(1.0, spam_prob))  # 0~1 범위 제한
            else:
                spam_prob = 0.5

            # 라벨 및 신뢰도 결정
            if spam_prob >= 0.7:
                label = "SPAM"
                confidence = "high" if spam_prob >= 0.85 else "medium"
            elif spam_prob <= 0.3:
                label = "HAM"
                confidence = "high" if spam_prob <= 0.15 else "medium"
            else:
                label = "UNCERTAIN"
                confidence = "low"

            return {
                "spam_prob": spam_prob,
                "confidence": confidence,
                "label": label,
            }

        except Exception as e:
            print(f"[WARNING] LLaMA 스팸 분류 실패: {e}")
            return {
                "spam_prob": 0.5,
                "confidence": "low",
                "label": "UNCERTAIN",
            }
