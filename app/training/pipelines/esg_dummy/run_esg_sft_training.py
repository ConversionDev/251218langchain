"""
ESG error_type SFT 학습: esg_error_chat.jsonl → EXAONE LoRA 파인튜닝.

- esg_error_chat.jsonl (messages 형식) 자동 90:10 train/val 분할 (label 기준 stratify)
- 역량 SFT와 동일: transformers + PEFT + bitsandbytes 4bit, apply_chat_template

실행:
  cd C:\\dev\\RAG
  python -m app.training.pipelines.esg_dummy.run_esg_sft_training

먼저 run_esg_to_chat_format.py 로 esg_error_chat.jsonl 생성 필요.
"""

import json
import os
import sys
import time
from pathlib import Path

_app_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_app_root) not in sys.path:
    sys.path.insert(0, str(_app_root))

os.environ["TRANSFORMERS_TRUST_REMOTE_CODE"] = "true"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["UNSLOTH_DISABLE_TRAINER_PATCH"] = "1"

from core.resource_manager import setup_unsloth_cache  # type: ignore  # noqa: E402

setup_unsloth_cache()

import torch  # noqa: E402
from datasets import Dataset  # noqa: E402
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training  # noqa: E402
from transformers import (  # noqa: E402
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
    TrainerState,
)
from sklearn.model_selection import train_test_split  # noqa: E402

try:
    from trl.trainer.sft_trainer import SFTTrainer as _OriginalSFTTrainer  # type: ignore
    from trl.trainer.sft_config import SFTConfig  # type: ignore
    SFTTrainer = _OriginalSFTTrainer
    print("[INFO] EXAONE ESG SFT: 원본 TRL SFTTrainer 사용 (Unsloth 패치 비활성화)")
except ImportError:
    try:
        from trl import SFTTrainer, SFTConfig  # type: ignore
    except ImportError:
        SFTTrainer = None
        SFTConfig = None
        print("[ERROR] trl이 설치되지 않았습니다. pip install trl")

from core.paths import get_output_dir, get_esg_dummy_dir  # type: ignore  # noqa: E402


MODEL_ID = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"
MODEL_REVISION = "0ff6b5e"
INPUT_FILE = "esg_error_chat.jsonl"
OUTPUT_SUBDIR = "esg_adapters"
MAX_SEQ_LENGTH = 512  # ESG 슬롯 한 줄+라벨은 짧아 512면 충분, 1024보다 연산 감소


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _load_and_split_data(data_dir: Path, val_ratio: float = 0.1, seed: int = 42) -> tuple[Dataset, Dataset]:
    """esg_error_chat.jsonl 로드 후 train/val 분할 (label 기준 stratify)."""
    in_path = data_dir / INPUT_FILE
    train_path = data_dir / "esg_train.jsonl"
    val_path = data_dir / "esg_val.jsonl"

    if not in_path.exists():
        raise FileNotFoundError(f"파일 없음: {in_path}\n먼저 run_esg_to_chat_format.py를 실행하세요.")

    if train_path.exists() and val_path.exists():
        train_rows = _load_jsonl(train_path)
        val_rows = _load_jsonl(val_path)
        if train_rows and val_rows:
            print(f"[OK] 기존 파일 사용: Train {len(train_rows)}건, Val {len(val_rows)}건")
            return Dataset.from_list(train_rows), Dataset.from_list(val_rows)

    rows = []
    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("messages"):
                    rows.append(obj)
            except json.JSONDecodeError:
                continue

    if not rows:
        raise ValueError(f"유효한 데이터가 없습니다: {in_path}")

    labels = [r.get("label", "normal") for r in rows]
    try:
        train_rows, val_rows = train_test_split(
            rows, test_size=val_ratio, random_state=seed, stratify=labels
        )
    except ValueError:
        train_rows, val_rows = train_test_split(rows, test_size=val_ratio, random_state=seed)
    for path, data in [(train_path, train_rows), (val_path, val_rows)]:
        with path.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[OK] Train {len(train_rows)}건, Val {len(val_rows)}건 → {train_path.name}, {val_path.name}")
    return Dataset.from_list(train_rows), Dataset.from_list(val_rows)


class SpeedETACallback(TrainerCallback):
    """학습 중 속도·예상 완료 시간 로그."""

    def __init__(self, log_every: int = 50):
        self.log_every = log_every
        self._train_start: float | None = None

    def on_train_begin(self, args, state: TrainerState, control, **kwargs):
        self._train_start = time.perf_counter()
        total = getattr(state, "max_steps", None) or 0
        if total:
            print(f"[INFO] 총 스텝: {total}, 로깅 간격: {args.logging_steps} (속도·예상 완료 시각은 로그에 출력)")

    def on_log(self, args, state: TrainerState, control, logs=None, **kwargs):
        if logs is None or state.global_step <= 0:
            return
        if state.global_step % self.log_every != 0:
            return
        total = getattr(state, "max_steps", None) or 0
        if total <= 0:
            return
        elapsed = time.perf_counter() - (self._train_start or 0)
        if elapsed <= 0:
            return
        speed = state.global_step / elapsed  # steps per second
        remaining_steps = total - state.global_step
        eta_sec = remaining_steps / speed if speed > 0 else 0
        eta_min = eta_sec / 60
        samples_per_sec = logs.get("train_samples_per_second")
        sps_str = f"  샘플/초: {samples_per_sec:.2f}" if samples_per_sec is not None else ""
        pct = 100 * state.global_step / total
        print(f"  [진행] step {state.global_step}/{total} ({pct:.1f}%)  step/s: {speed:.2f}{sps_str}  예상 남은 시간: 약 {eta_min:.1f}분")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="ESG error_type EXAONE SFT")
    parser.add_argument("--resume", action="store_true", help="output_dir 내 최신 체크포인트에서 이어받기")
    args = parser.parse_args()

    if SFTTrainer is None:
        sys.exit(1)

    if not torch.cuda.is_available():
        print("[ERROR] CUDA가 필요합니다. GPU를 확인하세요.")
        sys.exit(1)

    print("=" * 60)
    print("[INFO] ESG error_type EXAONE SFT 학습 시작")
    print("=" * 60)

    data_dir = get_esg_dummy_dir()
    output_dir = get_output_dir() / "exaone" / OUTPUT_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[Step 1] 데이터 로드 및 train/val 분할")
    train_dataset, val_dataset = _load_and_split_data(data_dir)

    print("\n[Step 2] 토크나이저 로드")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        trust_remote_code=True,
        model_max_length=MAX_SEQ_LENGTH,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print("\n[Step 3] 모델 로드 (4-bit 양자화 + LoRA)")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        quantization_config=bnb_config,
        device_map="cuda:0",
        trust_remote_code=True,
        dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    def formatting_func(example: dict) -> str:
        msgs = example.get("messages", [])
        if not msgs:
            return ""
        text = tokenizer.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=False,
        )
        return text if isinstance(text, str) else ""

    print("\n[Step 4] SFT 학습 실행")
    if SFTConfig is None:
        raise ImportError("SFTConfig를 불러올 수 없습니다. trl 버전을 확인하세요.")

    sft_config = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=2,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        warmup_steps=50,
        logging_steps=25,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=False,
        bf16=torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        logging_dir=str(output_dir / "logs"),
        remove_unused_columns=False,
        dataloader_num_workers=2,
        gradient_checkpointing=False,
        max_length=MAX_SEQ_LENGTH,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        formatting_func=formatting_func,
        processing_class=tokenizer,
        callbacks=[SpeedETACallback(log_every=50)],
    )

    resume_from = None
    if args.resume:
        # output_dir에서 checkpoint-* 중 최신(스텝 최대) 선택
        checkpoints = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")]
        if checkpoints:
            def _step(p: Path) -> int:
                try:
                    return int(p.name.replace("checkpoint-", ""))
                except ValueError:
                    return -1
            latest = max(checkpoints, key=_step)
            resume_from = str(latest)
            print(f"[INFO] 이어받기: {latest.name}")
        else:
            print("[INFO] 체크포인트 없음, 처음부터 학습")

    trainer_stats = trainer.train(resume_from_checkpoint=resume_from)

    if hasattr(trainer_stats, "metrics") and trainer_stats.metrics:
        m = trainer_stats.metrics
        print()
        print("[INFO] 학습 통계:")
        if m.get("train_runtime") is not None:
            print(f"  - 총 학습 시간: {m['train_runtime']:.2f}초 ({m['train_runtime']/60:.1f}분)")
        if m.get("train_steps") is not None:
            print(f"  - 총 스텝: {m['train_steps']}")
        if m.get("train_samples_per_second") is not None:
            print(f"  - 초당 샘플: {m['train_samples_per_second']:.2f}")
        print()

    print("\n[Step 5] 모델 저장")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[OK] 학습 완료: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
