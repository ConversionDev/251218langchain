"""
LLaMA 스팸 분류 Fine-tuning (Unsloth + LoRA)

Unsloth를 사용하여 LLaMA 모델을 2~5배 빠르게 fine-tuning합니다.
"""

import os
import sys
from pathlib import Path

# ============================================================================
# Windows 환경 설정 (멀티프로세싱 및 TorchInductor 문제 방지)
# ============================================================================

# Unsloth 캐시가 app/training/ 디렉토리에 생성되도록 작업 디렉토리 변경
training_dir = Path(__file__).parent.resolve()
original_cwd = os.getcwd()
os.chdir(training_dir)

# OpenMP 충돌 방지
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

# TorchInductor/Triton 비활성화 (Windows에서 FileNotFoundError 방지)
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHINDUCTOR_DISABLE"] = "1"

# 토크나이저 및 데이터셋 병렬화 비활성화 (Windows 안정성)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_DATASETS_MULTIPROCESSING_MAX_WORKERS"] = "0"
os.environ["HF_DATASETS_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_DATASETS_IN_MEMORY_MAX_SIZE"] = "0"

# CUDA 동기 실행 (디버깅 및 안정성)
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# Windows multiprocessing 설정
if sys.platform == "win32":
    import multiprocessing

    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

# ============================================================================
# Unsloth를 가장 먼저 import해야 최적화가 적용됨
# ============================================================================
import unsloth  # noqa: E402, F401
from unsloth import FastLanguageModel  # noqa: E402

# app/ 디렉토리를 Python 경로에 추가
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from typing import Any, Dict, List, Optional

import torch
from datasets import Dataset  # noqa: E402
from domain.spam.services.utils import (  # type: ignore
    extract_email_metadata,
    format_email_text,
    get_data_dir,
    get_output_dir,
    load_jsonl,
)
from transformers import DataCollatorForSeq2Seq, TrainingArguments  # noqa: E402
from trl import SFTTrainer  # noqa: E402


class LLaMATrainer:
    """LLaMA 스팸 분류 Unsloth LoRA Fine-tuning 클래스."""

    def __init__(
        self,
        model_id: str = "unsloth/Llama-3.2-3B-Instruct",
        output_dir: Optional[Path] = None,
        max_seq_length: int = 512,
        load_in_4bit: bool = True,
    ):
        """초기화.

        Args:
            model_id: HuggingFace 모델 ID (unsloth 최적화 모델 권장)
            output_dir: 출력 디렉토리 (None이면 자동 생성)
            max_seq_length: 최대 시퀀스 길이
            load_in_4bit: 4-bit 양자화 사용 여부
        """
        self.model_id = model_id
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        
        # GPU 필수 확인
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA가 사용 불가능합니다. GPU가 필요합니다.\n"
                "torch.cuda.is_available()이 False입니다."
            )
        
        self.device = "cuda"

        # 출력 디렉토리
        if output_dir is None:
            output_dir = get_output_dir() / "llama" / "adapters"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 모델 및 토크나이저
        self.tokenizer = None
        self.model = None

    def load_model(self) -> None:
        """Unsloth를 사용하여 모델 및 토크나이저 로드."""
        print("=" * 60)
        print("[INFO] Unsloth LLaMA 모델 로딩 시작")
        print("=" * 60)
        print(f"모델 ID: {self.model_id}")
        print(f"디바이스: {self.device}")
        print(f"4-bit 양자화: {self.load_in_4bit}")
        print(f"최대 시퀀스 길이: {self.max_seq_length}")
        print()

        try:
            # Unsloth FastLanguageModel로 모델 + 토크나이저 동시 로드
            print("[Step 1] Unsloth 모델 로딩 중...")
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_id,
                max_seq_length=self.max_seq_length,
                dtype=None,  # 자동 감지
                load_in_4bit=self.load_in_4bit,
            )
            print("[OK] 모델 로딩 완료")
            print()

            # LoRA 어댑터 추가
            print("[Step 2] LoRA 어댑터 설정 중...")
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                r=16,
                target_modules=[
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ],
                lora_alpha=16,
                lora_dropout=0,  # Unsloth에서는 0 권장
                bias="none",
                use_gradient_checkpointing="unsloth",  # 메모리 절약
                random_state=42,
            )
            print("[OK] LoRA 어댑터 설정 완료")
            print()

            # 학습 가능한 파라미터 출력
            self.model.print_trainable_parameters()

            print()
            print("=" * 60)
            print("[OK] Unsloth LLaMA 모델 로딩 완료!")
            print("=" * 60)
            print()

        except Exception as e:
            print(f"[ERROR] 모델 로딩 실패: {e}")
            import traceback

            traceback.print_exc()
            raise

    def prepare_dataset(self, sft_data: List[Dict[str, Any]]) -> Dataset:
        """SFT 데이터를 프롬프트 형식으로 변환.

        Args:
            sft_data: SFT 형식 데이터 리스트

        Returns:
            HuggingFace Dataset
        """
        print("[INFO] 데이터셋 준비 중...")
        texts = []

        for item in sft_data:
            # 이메일 메타데이터 추출
            email_metadata = extract_email_metadata(item)
            email_text = format_email_text(email_metadata)

            # 라벨 추출 (output.action에서)
            output = item.get("output", {})
            action = output.get("action", "")

            # BLOCK = spam, ALLOW = ham
            if action == "BLOCK":
                label = "0.95"  # 스팸 확률 높음
            elif action == "ALLOW":
                label = "0.05"  # 스팸 확률 낮음
            else:
                continue

            # Unsloth 프롬프트 형식
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

당신은 이메일 스팸 분류 전문가입니다. 이메일을 분석하여 스팸 확률을 0.0~1.0 사이 숫자로 답변하세요.<|eot_id|><|start_header_id|>user<|end_header_id|>

{email_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

스팸 확률: {label}<|eot_id|>"""

            texts.append(prompt)

        print(f"[OK] 데이터 준비 완료: {len(texts)}개")
        print()

        # Dataset 생성
        dataset = Dataset.from_dict({"text": texts})

        return dataset

    def train(
        self,
        train_data: List[Dict[str, Any]],
        val_data: Optional[List[Dict[str, Any]]] = None,
        num_epochs: int = 3,
        per_device_train_batch_size: int = 8,
        per_device_eval_batch_size: int = 8,
        learning_rate: float = 2e-4,
        warmup_steps: int = 10,
        logging_steps: int = 10,
        save_steps: int = 100,
        save_total_limit: int = 3,
        gradient_accumulation_steps: int = 4,
    ) -> Path:
        """Unsloth LoRA Fine-tuning 실행.

        Args:
            train_data: 학습 데이터 (SFT 형식)
            val_data: 검증 데이터 (SFT 형식, None이면 train에서 분할)
            num_epochs: 학습 에포크 수
            per_device_train_batch_size: 디바이스당 학습 배치 크기
            per_device_eval_batch_size: 디바이스당 평가 배치 크기
            learning_rate: 학습률
            warmup_steps: 워밍업 스텝 수
            logging_steps: 로깅 스텝 수
            save_steps: 저장 스텝 수
            save_total_limit: 최대 체크포인트 수
            gradient_accumulation_steps: 그래디언트 누적 스텝 수

        Returns:
            학습된 모델 경로
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("먼저 load_model()을 호출하세요.")

        print("=" * 60)
        print("[INFO] Unsloth LoRA Fine-tuning 시작")
        print("=" * 60)
        print()

        # 데이터셋 준비
        train_dataset = self.prepare_dataset(train_data)

        if val_data is None:
            # train에서 10% 분할
            split_dataset = train_dataset.train_test_split(test_size=0.1, seed=42)
            train_dataset = split_dataset["train"]
            val_dataset = split_dataset["test"]
        else:
            val_dataset = self.prepare_dataset(val_data)

        print(f"[INFO] 학습 데이터: {len(train_dataset)}개")
        print(f"[INFO] 검증 데이터: {len(val_dataset)}개")
        print()

        # TrainingArguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            per_device_eval_batch_size=per_device_eval_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            save_total_limit=save_total_limit,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            eval_strategy="steps",
            eval_steps=save_steps,
            save_strategy="steps",
            logging_dir=str(self.output_dir / "logs"),
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=42,
        )

        # SFTTrainer 사용 (Unsloth 최적화)
        # formatting_func을 사용하여 데이터셋의 "text" 필드를 처리
        def formatting_func(examples):
            return examples["text"]

        trainer = SFTTrainer(
            model=self.model,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            formatting_func=formatting_func,
            max_seq_length=self.max_seq_length,
            data_collator=DataCollatorForSeq2Seq(tokenizer=self.tokenizer),
            args=training_args,
        )

        # 학습 실행
        print("[INFO] 학습 시작...")
        trainer_stats = trainer.train()

        # 학습 통계 출력
        print()
        print("[INFO] 학습 통계:")
        print(f"  - 총 학습 시간: {trainer_stats.metrics['train_runtime']:.2f}초")
        print(
            f"  - 초당 샘플 수: {trainer_stats.metrics['train_samples_per_second']:.2f}"
        )
        print()

        # 모델 저장 (LoRA 어댑터만)
        final_model_path = self.output_dir / "final_model"
        self.model.save_pretrained(str(final_model_path))
        self.tokenizer.save_pretrained(str(final_model_path))

        print()
        print("=" * 60)
        print("[OK] Unsloth LoRA Fine-tuning 완료!")
        print(f"어댑터 경로: {final_model_path}")
        print("=" * 60)
        print()

        return final_model_path

    def save_merged_model(self, output_path: Optional[Path] = None) -> Path:
        """LoRA 어댑터를 base 모델에 병합하여 저장.

        Args:
            output_path: 출력 경로 (None이면 자동 생성)

        Returns:
            병합된 모델 경로
        """
        if output_path is None:
            output_path = self.output_dir / "merged_model"

        print("[INFO] 모델 병합 중...")
        self.model.save_pretrained_merged(
            str(output_path),
            self.tokenizer,
            save_method="merged_16bit",
        )
        print(f"[OK] 병합된 모델 저장: {output_path}")

        return output_path


def main():
    """메인 실행 함수."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Unsloth LLaMA 스팸 분류 LoRA Fine-tuning"
    )
    parser.add_argument(
        "--train_path",
        type=str,
        default=None,
        help="학습 데이터 경로 (None이면 자동 탐지)",
    )
    parser.add_argument(
        "--val_path",
        type=str,
        default=None,
        help="검증 데이터 경로 (None이면 train에서 분할)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="출력 디렉토리 (None이면 자동 생성)",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="unsloth/Llama-3.2-3B-Instruct",
        help="HuggingFace 모델 ID (unsloth 최적화 모델 권장)",
    )
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=3,
        help="학습 에포크 수 (기본값: 3)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="배치 크기 (기본값: 8, Unsloth로 더 큰 배치 가능)",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="학습률 (기본값: 2e-4)",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=512,
        help="최대 시퀀스 길이 (기본값: 512)",
    )

    args = parser.parse_args()

    # 경로 자동 탐지
    if args.train_path is None:
        data_dir = get_data_dir() / "sft_dataset" / "processed"
        args.train_path = str(data_dir / "train.jsonl")

    if args.val_path:
        args.val_path = str(Path(args.val_path))

    # 데이터 로드
    print("[INFO] 데이터 로드 중...")
    train_data = load_jsonl(Path(args.train_path))
    val_data = None
    if args.val_path:
        val_data = load_jsonl(Path(args.val_path))
    print(f"[OK] Train: {len(train_data)}개")
    if val_data:
        print(f"[OK] Val: {len(val_data)}개")
    print()

    # Trainer 생성 및 학습
    trainer = LLaMATrainer(
        model_id=args.model_id,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        max_seq_length=args.max_seq_length,
    )
    trainer.load_model()
    trainer.train(
        train_data=train_data,
        val_data=val_data,
        num_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()
