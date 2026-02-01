"""
Llama 3.2B 시멘틱 분류 Fine-tuning (Unsloth + LoRA)

Unsloth를 사용하여 Llama 3.2B 모델을 시멘틱 분류 태스크로 fine-tuning합니다.
규칙 기반(RULE_BASED), 정책 기반(POLICY_BASED), 차단(BLOCK) 판단을 학습합니다.
"""

import os
import shutil
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# 작업 디렉토리를 리소스 매니저로 변경
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
import torch  # noqa: E402

torch._dynamo.config.disable = True
torch._dynamo.config.suppress_errors = True

# ============================================================================
# Unsloth를 가장 먼저 import해야 최적화가 적용됨
# ============================================================================
import unsloth  # noqa: E402, F401

from unsloth import FastLanguageModel  # noqa: E402

from datasets import Dataset  # noqa: E402
from transformers import DataCollatorForSeq2Seq, TrainingArguments  # noqa: E402
from trl import SFTTrainer  # noqa: E402


class SemanticClassifierTrainer:
    """Llama 3.2B 시멘틱 분류 Unsloth LoRA Fine-tuning 클래스."""

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

        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = app_dir / "artifacts" / "semantic_classifier" / "adapters"
        else:
            output_dir = Path(output_dir)

        self.output_dir = output_dir
        self._setup_output_directory()

        # 모델 및 토크나이저
        self.tokenizer = None
        self.model = None

    def _setup_output_directory(self) -> None:
        """출력 디렉토리 설정 및 기존 모델 처리."""
        # 기존 모델이 있으면 덮어쓰기
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_model(self) -> None:
        """Unsloth를 사용하여 모델 및 토크나이저 로드."""
        print("=" * 60)
        print("[INFO] Unsloth Llama 3.2B 모델 로딩 시작")
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
                lora_alpha=32,
                lora_dropout=0.05,
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
            print("[OK] Unsloth Llama 3.2B 모델 로딩 완료!")
            print("=" * 60)
            print()

        except Exception as e:
            print(f"[ERROR] 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            raise

    def load_jsonl_dataset(self, file_path: Path) -> List[Dict[str, Any]]:
        """JSONL 파일을 로드하여 ChatML 형식 데이터 반환.

        Args:
            file_path: JSONL 파일 경로

        Returns:
            ChatML 형식 데이터 리스트
        """
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    # messages 형식 검증
                    if "messages" in item and isinstance(item["messages"], list):
                        data.append(item)
                    else:
                        print(f"[WARNING] 라인 {line_num}: 'messages' 필드가 없거나 형식이 올바르지 않습니다.")
                except json.JSONDecodeError as e:
                    print(f"[WARNING] 라인 {line_num}: JSON 파싱 오류 - {e}")
                    continue

        print(f"[OK] 데이터셋 로드 완료: {len(data)}개 샘플")
        return data

    def prepare_dataset(self, chatml_data: List[Dict[str, Any]]) -> Dataset:
        """ChatML 형식 데이터를 Unsloth 학습 형식으로 변환.

        Args:
            chatml_data: ChatML 형식 데이터 리스트

        Returns:
            HuggingFace Dataset
        """
        print("[INFO] 데이터셋 준비 중...")
        texts = []

        for item in chatml_data:
            messages = item.get("messages", [])
            if not messages:
                continue

            # ChatML 형식을 Llama 3 토큰 형식으로 변환
            # Llama 3 형식: <|begin_of_text|><|start_header_id|>role<|end_header_id|>\n\ncontent<|eot_id|>
            formatted_text = "<|begin_of_text|>"

            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "system":
                    formatted_text += f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
                elif role == "user":
                    formatted_text += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
                elif role == "assistant":
                    formatted_text += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"

            texts.append(formatted_text)

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
        warmup_steps: int = 50,
        logging_steps: int = 10,
        save_steps: int = 500,
        save_total_limit: int = 3,
        gradient_accumulation_steps: int = 2,
        eval_strategy: str = "steps",
        eval_steps: Optional[int] = None,
        disable_eval: bool = False,
    ) -> Path:
        """Unsloth LoRA Fine-tuning 실행.

        Args:
            train_data: 학습 데이터 (ChatML 형식)
            val_data: 검증 데이터 (ChatML 형식, None이면 train에서 분할)
            num_epochs: 학습 에포크 수
            per_device_train_batch_size: 디바이스당 학습 배치 크기
            per_device_eval_batch_size: 디바이스당 평가 배치 크기
            learning_rate: 학습률
            warmup_steps: 워밍업 스텝 수
            logging_steps: 로깅 스텝 수
            save_steps: 저장 스텝 수
            save_total_limit: 최대 체크포인트 수
            gradient_accumulation_steps: 그래디언트 누적 스텝 수
            eval_strategy: 평가 전략
            eval_steps: 평가 빈도 (None이면 save_steps 사용)
            disable_eval: 평가 비활성화

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

        # 평가 전략 설정 (load_best_model_at_end 사용 시 eval_strategy와 save_strategy 일치 필수)
        if disable_eval:
            final_eval_strategy = "no"
            final_eval_steps = None
            final_save_strategy = "steps"
        else:
            final_eval_strategy = eval_strategy
            if final_eval_strategy == "epoch":
                final_eval_steps = None
                final_save_strategy = "epoch"
            else:
                final_eval_steps = eval_steps if eval_steps is not None else save_steps
                final_save_strategy = "steps"

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
            # Mixed precision
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            # 평가 설정
            eval_strategy=final_eval_strategy,
            eval_steps=final_eval_steps,
            # 체크포인트 설정 (eval과 save 단위 일치해야 load_best_model_at_end 사용 가능)
            save_strategy=final_save_strategy,
            save_on_each_node=False,
            save_safetensors=True,
            # 로깅 설정
            logging_dir=str(self.output_dir / "logs"),
            report_to="none",
            # 옵티마이저 설정
            optim="adamw_8bit",
            weight_decay=0.01,
            # 학습률 스케줄러
            lr_scheduler_type="cosine",
            # 안정성 설정
            seed=42,
            max_grad_norm=1.0,
            gradient_checkpointing=True,
            # 체크포인트 복구 설정
            resume_from_checkpoint=False,
            overwrite_output_dir=True,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            # 데이터 로더 설정 (Windows 안정성)
            dataloader_num_workers=0,
            dataloader_pin_memory=False,
        )

        # SFTTrainer 사용
        def formatting_func(examples):
            return examples["text"]

        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=train_dataset,
            eval_dataset=val_dataset if not disable_eval else None,
            formatting_func=formatting_func,
            max_seq_length=self.max_seq_length,
            data_collator=DataCollatorForSeq2Seq(tokenizer=self.tokenizer),
            args=training_args,
        )

        # 학습 실행
        print("[INFO] 학습 시작...")
        try:
            trainer_stats = trainer.train()

            # 학습 통계 출력 (metrics 키는 transformers/trl 버전별로 상이함 → .get() 사용)
            print()
            print("[INFO] 학습 통계:")
            m = trainer_stats.metrics
            if m.get("train_runtime") is not None:
                print(f"  - 총 학습 시간: {m['train_runtime']:.2f}초")
            if m.get("train_steps") is not None:
                print(f"  - 총 스텝: {m['train_steps']}")
            elif m.get("num_train_epochs") is not None and m.get("train_samples") is not None:
                # 일부 버전: epoch·샘플 수만 있는 경우
                print(f"  - 학습 에포크: {m['num_train_epochs']}, 샘플 수: {m['train_samples']}")
            if m.get("train_samples_per_second") is not None:
                print(f"  - 초당 샘플: {m['train_samples_per_second']:.2f}")
            print()

            # 최종 모델 저장
            print("[INFO] 최종 모델 저장 중...")
            trainer.save_model()
            self.tokenizer.save_pretrained(self.output_dir)
            print(f"[OK] 모델 저장 완료: {self.output_dir}")
            print()

            print("=" * 60)
            print("[OK] 학습 완료!")
            print("=" * 60)
            print(f"모델 경로: {self.output_dir}")
            print()

            return self.output_dir

        except Exception as e:
            print(f"[ERROR] 학습 실패: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    """메인 실행 함수."""
    # 데이터셋 경로
    dataset_path = app_dir / "data" / "soccer" / "llama_training_dataset.jsonl"

    # 파일 존재 확인
    if not dataset_path.exists():
        print(f"[ERROR] 데이터셋 파일을 찾을 수 없습니다: {dataset_path}")
        return

    print("=" * 60)
    print("[INFO] 시멘틱 분류 학습 시작")
    print("=" * 60)
    print(f"데이터셋: {dataset_path}")
    print()

    # Trainer 생성
    trainer = SemanticClassifierTrainer(
        model_id="unsloth/Llama-3.2-3B-Instruct",
        max_seq_length=512,
        load_in_4bit=True,
    )

    # 모델 로드
    trainer.load_model()

    # 데이터셋 로드
    print("[INFO] 데이터셋 로드 중...")
    all_data = trainer.load_jsonl_dataset(dataset_path)
    print()

    # Train/Val 분할 (80/20)
    split_idx = int(len(all_data) * 0.8)
    train_data = all_data[:split_idx]
    val_data = all_data[split_idx:]

    print(f"[INFO] Train 데이터: {len(train_data)}개")
    print(f"[INFO] Validation 데이터: {len(val_data)}개")
    print()

    # 학습 실행 (5 에포크 최적화 설정 - 속도와 성능 균형)
    try:
        output_path = trainer.train(
            train_data=train_data,
            val_data=val_data,
            num_epochs=5,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=16,
            learning_rate=2e-4,
            warmup_steps=50,
            logging_steps=10,
            save_steps=500,
            save_total_limit=3,
            gradient_accumulation_steps=1,
            eval_strategy="epoch",
            eval_steps=None,
        )

        print("[OK] 학습 완료!")
        print(f"[INFO] 학습된 모델: {output_path}")

    except Exception as e:
        print(f"[ERROR] 학습 실패: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
