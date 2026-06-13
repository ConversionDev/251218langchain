"""
LLaMA 스팸 분류 Fine-tuning (Unsloth + LoRA)

Unsloth를 사용하여 LLaMA 모델을 2~5배 빠르게 fine-tuning합니다.
"""

import os
import shutil
import sys
from pathlib import Path

# ============================================================================
# Windows 환경 설정 (멀티프로세싱 및 TorchInductor 문제 방지)
# ============================================================================

# app/ 디렉토리를 Python 경로에 추가 (작업 디렉토리 변경 전에)
app_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Unsloth 캐시 설정 (작업 디렉토리 변경 전에 실행)
from core.resource_manager import setup_unsloth_cache  # type: ignore
setup_unsloth_cache()  # 절대 경로로 환경 변수 설정

# 작업 디렉토리를 리소스 매니저로 변경 (방법 1: 근본 원인 해결)
# Unsloth가 작업 디렉토리 기준으로 캐시를 생성하므로 리소스 매니저 위치에 직접 생성되도록 함
from core.paths import get_resource_manager_dir  # type: ignore
resource_manager_dir = get_resource_manager_dir()
os.chdir(resource_manager_dir)

# training_dir는 다른 경로 참조에 필요하므로 유지
training_dir = Path(__file__).resolve().parent.parent.parent.parent

# OpenMP 충돌 방지
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# TorchInductor/Triton 비활성화
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
# torch._dynamo 전역 비활성화
# ============================================================================
# Unsloth의 하드코딩된 @torch.compile 데코레이터를 무시하기 위해 비활성화
import torch  # noqa: E402

torch._dynamo.config.disable = True
torch._dynamo.config.suppress_errors = True

# ============================================================================
# Unsloth를 가장 먼저 import해야 최적화가 적용됨
# ============================================================================
import unsloth  # noqa: E402, F401

from unsloth import FastLanguageModel  # noqa: E402

from typing import Any, Dict, List, Optional

from datasets import Dataset  # noqa: E402
from core.paths import (  # type: ignore
    get_llama_adapters_dir,
    get_project_root,
    get_spam_sft_dir,
)
from domain.shared.utils import (  # type: ignore
    extract_email_metadata,
    format_email_text,
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
        max_seq_length: int = 1024,  # 전략 A: 데이터 전부 활용·본문 미절단 (512: 더 빠름, 2048: 더 긴 메일)
        load_in_4bit: bool = True,
    ):
        """초기화.

        Args:
            model_id: HuggingFace 모델 ID (unsloth 최적화 모델 권장)
            output_dir: 출력 디렉토리 (None이면 자동 생성, Exaone과 동일한 구조 사용)
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

        # 출력 디렉토리 설정 (ExaOne과 동일 전략: core.paths.get_llama_adapters_dir)
        if output_dir is None:
            output_dir = get_llama_adapters_dir()
        else:
            output_dir = Path(output_dir)

        self.output_dir = output_dir
        self._setup_output_directory()

        # 모델 및 토크나이저
        self.tokenizer = None
        self.model = None

    def _setup_output_directory(self) -> None:
        """출력 디렉토리 설정 및 기존 모델 처리 (Exaone과 동일한 구조, 덮어쓰기)."""
        # 기존 모델이 있으면 덮어쓰기
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

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
                r=8,  # 1 에포크 최적화: 16 -> 8 (메모리 절약, 속도 향상)
                target_modules=[
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ],
                lora_alpha=8,  # 1 에포크 최적화: 16 -> 8 (r과 동일하게)
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

    def prepare_dataset(
        self,
        sft_data: List[Dict[str, Any]],
        tokenizer: Any = None,
    ) -> Dataset:
        """SFT 데이터를 프롬프트 형식으로 변환.

        app/data/spam 소스 파일은 읽기만 하고 수정하지 않음.
        본문은 잘리지 않음. tokenizer가 주어지면 max_seq_length 초과 샘플만 학습에서 제외 → Unsloth 길이 오류 방지.
        """
        print("[INFO] 데이터셋 준비 중...")
        texts = []
        max_tokens = self.max_seq_length
        n_skipped = 0

        for item in sft_data:
            email_metadata = extract_email_metadata(item)
            email_text = format_email_text(email_metadata)

            output = item.get("output", {})
            action = output.get("action", "")
            if action == "BLOCK":
                label = "0.95"
            elif action == "ALLOW":
                label = "0.05"
            else:
                continue

            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

당신은 이메일 스팸 분류 전문가입니다. 이메일을 분석하여 스팸 확률을 0.0~1.0 사이 숫자로 답변하세요.<|eot_id|><|start_header_id|>user<|end_header_id|>

{email_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

스팸 확률: {label}<|eot_id|>"""

            # 본문 훼손 없음: 초과 샘플만 제외. Unsloth 길이 오류 방지.
            if tokenizer is not None:
                ids = tokenizer.encode(prompt, add_special_tokens=False, truncation=False)
                if len(ids) > max_tokens:
                    n_skipped += 1
                    continue

            texts.append(prompt)

        if n_skipped:
            print(f"[INFO] 본문 미절단 원칙: max_seq_length({max_tokens}) 초과로 {n_skipped}건 제외 (학습에 사용 안 함)")
        print(f"[OK] 데이터 준비 완료: {len(texts)}개")
        print()

        return Dataset.from_dict({"text": texts})

    def train(
        self,
        train_data: List[Dict[str, Any]],
        val_data: Optional[List[Dict[str, Any]]] = None,
        num_epochs: int = 3,  # 3 에포크: 데이터 반영·안정성 (속도와 균형)
        per_device_train_batch_size: int = 32,
        per_device_eval_batch_size: int = 32,
        learning_rate: float = 2e-4,  # 3 에포크용 안정 수렴
        warmup_steps: int = 50,  # 3 에포크 시 워밍업 여유
        logging_steps: int = 10,
        save_steps: int = 150,  # 에포크당 2회 전후 체크포인트
        save_total_limit: int = 3,  # 최근 3개 체크포인트 유지
        gradient_accumulation_steps: int = 1,
        eval_strategy: str = "epoch",  # 에포크 끝 평가
        eval_steps: Optional[int] = None,
        disable_eval: bool = False,  # 평가 기본 활성화 (모니터링 중요)
    ) -> Path:
        """Unsloth LoRA Fine-tuning 실행.

        Args:
            train_data: 학습 데이터 (SFT 형식)
            val_data: 검증 데이터 (SFT 형식, None이면 train에서 분할)
            num_epochs: 학습 에포크 수 (기본값: 3, 데이터·안정성)
            per_device_train_batch_size: 디바이스당 학습 배치 크기 (기본값: 32)
            per_device_eval_batch_size: 디바이스당 평가 배치 크기 (기본값: 32)
            learning_rate: 학습률 (기본값: 2e-4, 3 에포크 안정 수렴)
            warmup_steps: 워밍업 스텝 수 (기본값: 50)
            logging_steps: 로깅 스텝 수
            save_steps: 저장 스텝 수 (기본값: 150)
            save_total_limit: 최대 체크포인트 수 (기본값: 3)
            gradient_accumulation_steps: 그래디언트 누적 스텝 수 (기본값: 1)
            eval_strategy: 평가 전략 (기본값: "epoch")
            eval_steps: 평가 빈도 (None이면 eval_strategy에 따라 결정)
            disable_eval: 평가 비활성화 (기본값: False, 평가 유지 권장)

        Returns:
            학습된 모델 경로
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("먼저 load_model()을 호출하세요.")

        print("=" * 60)
        print("[INFO] Unsloth LoRA Fine-tuning 시작")
        print("=" * 60)
        print()

        # 데이터셋 준비 (토크나이저로 길이 검사 → Unsloth max_seq_length 초과 방지)
        train_dataset = self.prepare_dataset(train_data, tokenizer=self.tokenizer)

        if val_data is None:
            # train에서 10% 분할
            split_dataset = train_dataset.train_test_split(test_size=0.1, seed=42)
            train_dataset = split_dataset["train"]
            val_dataset = split_dataset["test"]
        else:
            val_dataset = self.prepare_dataset(val_data, tokenizer=self.tokenizer)

        print(f"[INFO] 학습 데이터: {len(train_dataset)}개")
        print(f"[INFO] 검증 데이터: {len(val_dataset)}개")
        print()

        # 평가 전략 설정 (에포크 끝 평가)
        if disable_eval:
            final_eval_strategy = "no"
            final_eval_steps = None
        else:
            final_eval_strategy = eval_strategy
            if final_eval_strategy == "epoch":
                final_eval_steps = None
            else:
                final_eval_steps = eval_steps if eval_steps is not None else save_steps

        # TrainingArguments (안정성과 속도 균형 최적화)
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
            # Mixed precision (속도 최적화)
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            # 평가 설정 (안정성: 모니터링 유지)
            eval_strategy=final_eval_strategy,
            eval_steps=final_eval_steps,
            # 체크포인트 설정 (안정성: 충분한 체크포인트 보장)
            save_strategy="steps",
            save_on_each_node=False,  # 단일 노드 학습
            save_safetensors=True,  # 안전한 텐서 저장 형식
            # 로깅 설정
            logging_dir=str(self.output_dir / "logs"),
            report_to="none",  # 외부 로깅 비활성화 (속도 최적화)
            # 옵티마이저 설정 (메모리 최적화)
            optim="adamw_8bit",
            weight_decay=0.01,
            # 학습률 스케줄러 (속도 최적화: 빠른 수렴)
            lr_scheduler_type="cosine",
            # 안정성 설정
            seed=42,  # 재현성 보장
            max_grad_norm=1.0,  # 그래디언트 클리핑 (안정성)
            gradient_checkpointing=True,  # 메모리 절약 (이미 LoRA에서 설정됨)
            # 체크포인트 복구 설정 (안정성)
            resume_from_checkpoint=False,  # 명시적으로 새 학습 시작
            overwrite_output_dir=True,  # 기존 디렉토리 덮어쓰기
            load_best_model_at_end=False,
            # 데이터 로더 설정 (Windows 안정성)
            dataloader_num_workers=0,  # Windows 멀티프로세싱 문제 방지
            dataloader_pin_memory=False,  # Windows 안정성
        )

        # SFTTrainer 사용 (Unsloth 최적화)
        # formatting_func을 사용하여 데이터셋의 "text" 필드를 처리
        def formatting_func(examples):
            return examples["text"]

        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,  # Unsloth SFTTrainer에 필수 (fix_untrained_tokens에서 사용)
            train_dataset=train_dataset,
            eval_dataset=val_dataset if not disable_eval else None,
            formatting_func=formatting_func,
            max_seq_length=self.max_seq_length,
            data_collator=DataCollatorForSeq2Seq(tokenizer=self.tokenizer),
            args=training_args,
        )

        # 예상 총 스텝 수 (학습 전 안내)
        num_devices = max(1, torch.cuda.device_count())
        batch_size_effective = (
            per_device_train_batch_size
            * gradient_accumulation_steps
            * num_devices
        )
        total_steps = num_epochs * (
            (len(train_dataset) + batch_size_effective - 1) // batch_size_effective
        )
        print("[INFO] 학습 예상:")
        print(f"  - 예상 총 스텝: {total_steps}")
        print(f"  - 로깅: 매 {logging_steps}스텝, 체크포인트 저장: 매 {save_steps}스텝")
        print(f"  - 학습 중 진행률 표시되며, 종료 시 총 소요 시간·초당 샘플 수 출력")
        print()

        # 학습 시작 시 초기 체크포인트 저장 (학습 실패 시 보존)
        # save_total_limit에 포함되지 않으므로 별도로 보존
        initial_checkpoint = self.output_dir / "checkpoint-0"
        trainer.save_model(str(initial_checkpoint))
        print(f"[INFO] 초기 체크포인트 저장: {initial_checkpoint.name}")

        # 학습 실행 (예외 처리 포함)
        print("[INFO] 학습 시작...")
        try:
            trainer_stats = trainer.train()

            # 학습 통계 출력
            print()
            print("[INFO] 학습 통계:")
            print(f"  - 총 학습 시간: {trainer_stats.metrics['train_runtime']:.2f}초")
            print(
                f"  - 초당 샘플 수: {trainer_stats.metrics['train_samples_per_second']:.2f}"
            )
            print()
        except Exception:
            # 학습 실패 시에도 마지막 체크포인트 보존
            self._save_latest_checkpoint_as_final(trainer)
            raise

        # 모델 저장 (LoRA 어댑터만)
        final_model_path = self.output_dir / "final_model"
        try:
            self.model.save_pretrained(str(final_model_path))
            self.tokenizer.save_pretrained(str(final_model_path))
        except Exception:
            # 저장 실패 시 마지막 체크포인트를 final_model로 복사
            self._save_latest_checkpoint_as_final(trainer)

        print()
        print("=" * 60)
        print("[OK] Unsloth LoRA Fine-tuning 완료!")
        print(f"어댑터 경로: {final_model_path}")
        print("=" * 60)
        print()

        return final_model_path

    def _save_latest_checkpoint_as_final(self, trainer: SFTTrainer) -> None:
        """마지막 체크포인트를 final_model로 복사 (학습 실패 시 보존용)."""
        try:
            # 체크포인트 디렉토리 찾기
            checkpoint_dirs = [
                d for d in self.output_dir.iterdir()
                if d.is_dir() and d.name.startswith("checkpoint-")
            ]

            if checkpoint_dirs:
                # 가장 최신 체크포인트 찾기
                latest_checkpoint = max(
                    checkpoint_dirs,
                    key=lambda x: int(x.name.split("-")[1]) if x.name.split("-")[1].isdigit() else 0
                )

                final_model_path = self.output_dir / "final_model"
                if latest_checkpoint != final_model_path:
                    # 기존 final_model 삭제
                    if final_model_path.exists():
                        shutil.rmtree(final_model_path)

                    # 최신 체크포인트 복사
                    shutil.copytree(latest_checkpoint, final_model_path)
        except Exception:
            pass

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
        help="학습 에포크 수 (기본값: 3, 데이터·안정성)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="배치 크기 (기본값: 32)",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="학습률 (기본값: 2e-4, 3 에포크 안정 수렴)",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=1024,
        help="최대 시퀀스 길이 (기본값: 1024, 전략 A. 512=빠름, 2048=긴 메일 전부)",
    )
    parser.add_argument(
        "--disable_eval",
        action="store_true",
        help="평가 비활성화 (기본값: 활성화, 에포크 끝에 평가)",
    )

    args = parser.parse_args()

    # 경로: 상대 경로는 프로젝트 루트 기준 (os.chdir으로 cwd가 바뀌어도 동작하도록)
    project_root = get_project_root()
    if args.train_path is None:
        spam_sft = get_spam_sft_dir()
        exaone_synthetic = spam_sft / "exaone_synthetic.jsonl"
        args.train_path = str(exaone_synthetic)
        if not exaone_synthetic.exists():
            print("[INFO] exaone_synthetic.jsonl 없음. 먼저 run_exaone_generate_spam_sft 실행 후 재시도하세요.")
    else:
        train_path = Path(args.train_path)
        if not train_path.is_absolute():
            train_path = project_root / args.train_path
        args.train_path = str(train_path)
    if args.val_path:
        val_path = Path(args.val_path)
        if not val_path.is_absolute():
            val_path = project_root / args.val_path
        args.val_path = str(val_path)

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
        disable_eval=args.disable_eval,  # 기본값 False (평가 활성화)
    )


if __name__ == "__main__":
    main()
