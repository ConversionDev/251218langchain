"""LLaMA Gate - 요청 분류를 위한 경량 래퍼.

LLaMA 3.2 3B를 사용하여 규칙 기반/정책 기반 요청을 분류합니다.
Unsloth를 사용하여 추론 속도를 최적화합니다.

성능:
    - 속도: 기존 대비 2배 향상
    - 메모리: 60-80% 절약 (4bit 양자화)
    - Unsloth 자체 최적화 사용
"""

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHINDUCTOR_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from core.resource_manager import setup_unsloth_cache  # type: ignore

setup_unsloth_cache()

import torch  # noqa: E402

torch._dynamo.config.disable = True
torch._dynamo.config.suppress_errors = True

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

            if self.load_in_4bit:
                try:
                    import bitsandbytes  # noqa: F401
                    print("[INFO] bitsandbytes 확인 완료 - 4bit 양자화 사용")
                except ImportError:
                    raise ImportError(
                        "4bit 양자화를 사용하려면 bitsandbytes가 필요합니다. "
                        "설치: pip install bitsandbytes"
                    )

            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_id,
                max_seq_length=self.max_seq_length,
                dtype=None,
                load_in_4bit=self.load_in_4bit,
            )

            FastLanguageModel.for_inference(self.model)

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
            prompt = f"""다음 요청을 분석하여 규칙 기반 처리인지 정책 기반 처리인지 판단하세요.

요청 내용: {text}

규칙 기반 처리: 명확한 규칙이나 표준 절차로 처리 가능한 경우
정책 기반 처리: 복잡한 판단이나 해석이 필요한 경우

응답은 반드시 다음 중 하나로만 답변하세요:
- "rule_based"
- "policy_based"
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
            response = (
                self.tokenizer.decode(
                    outputs[0][input_length:], skip_special_tokens=True
                )
                .strip()
                .lower()
            )

            if "policy_based" in response or "policy" in response:
                return "policy_based"
            elif "rule_based" in response or "rule" in response:
                return "rule_based"
            else:
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
            body = email_data.get("body", "")[:500]

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

            import re

            match = re.search(r"(\d+\.?\d*)", response)
            if match:
                spam_prob = float(match.group(1))
                spam_prob = max(0.0, min(1.0, spam_prob))
            else:
                spam_prob = 0.5
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

    def classify_spam_batch(
        self, email_data_list: list[dict], batch_size: int = 32
    ) -> list[dict]:
        """이메일 스팸 분류 (배치 처리).

        Args:
            email_data_list: 이메일 메타데이터 리스트
            batch_size: 배치 크기

        Returns:
            스팸 분류 결과 리스트
        """
        if self.model is None or self.tokenizer is None:
            return [
                {"spam_prob": 0.5, "confidence": "low", "label": "UNCERTAIN"}
                for _ in email_data_list
            ]

        results = []
        import re

        # 배치 단위로 처리
        for batch_start in range(0, len(email_data_list), batch_size):
            batch_end = min(batch_start + batch_size, len(email_data_list))
            batch_data = email_data_list[batch_start:batch_end]

            try:
                prompts = []
                for email_data in batch_data:
                    subject = email_data.get("subject", "")
                    sender = email_data.get("sender", "")
                    body = email_data.get("body", "")[:500]

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
                    prompts.append(formatted)

                inputs = self.tokenizer(
                    prompts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
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

                for i, output in enumerate(outputs):
                    input_length = inputs["attention_mask"][i].sum().item()
                    response = (
                        self.tokenizer.decode(
                            output[input_length:], skip_special_tokens=True
                        )
                        .strip()
                        .lower()
                    )

                    match = re.search(r"(\d+\.?\d*)", response)
                    if match:
                        spam_prob = float(match.group(1))
                        spam_prob = max(0.0, min(1.0, spam_prob))
                    else:
                        spam_prob = 0.5
                    if spam_prob < 0.3:
                        label = "HAM"
                        confidence = "high" if spam_prob < 0.1 else "medium"
                    elif spam_prob > 0.7:
                        label = "SPAM"
                        confidence = "high" if spam_prob > 0.9 else "medium"
                    else:
                        label = "UNCERTAIN"
                        confidence = "low"

                    results.append(
                        {
                            "spam_prob": spam_prob,
                            "confidence": confidence,
                            "label": label,
                        }
                    )

            except Exception as e:
                print(f"[WARNING] 배치 처리 실패, 개별 처리로 전환: {e}")
                for email_data in batch_data:
                    try:
                        result = self.classify_spam(email_data)
                        results.append(result)
                    except Exception as e2:
                        print(f"[WARNING] 개별 처리도 실패: {e2}")
                        results.append(
                            {
                                "spam_prob": 0.5,
                                "confidence": "low",
                                "label": "UNCERTAIN",
                            }
                        )

        return results
