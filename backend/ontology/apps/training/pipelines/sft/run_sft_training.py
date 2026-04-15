"""
역량 SFT 학습: competency_qa_chat.jsonl → EXAONE LoRA 파인튜닝.

- competency_qa_chat.jsonl (messages 형식) 자동 90:10 train/val 분할
- transformers + PEFT + bitsandbytes 4bit (Unsloth 미사용)
- formatting_func으로 apply_chat_template 적용

실행:
  cd C:\\dev\\RAG
  python -m app.training.pipelines.sft.run_sft_training
"""

import json
import os
import sys
from pathlib import Path

# app/ 기준 경로
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
)
from sklearn.model_selection import train_test_split  # noqa: E402

try:
    from trl.trainer.sft_trainer import SFTTrainer as _OriginalSFTTrainer  # type: ignore
    from trl.trainer.sft_config import SFTConfig  # type: ignore
    SFTTrainer = _OriginalSFTTrainer
    print("[INFO] EXAONE 학습: 원본 TRL SFTTrainer 사용 (Unsloth 패치 비활성화)")
except ImportError:
    try:
        from trl import SFTTrainer, SFTConfig  # type: ignore
    except ImportError:
        SFTTrainer = None
        SFTConfig = None
        print("[ERROR] trl이 설치되지 않았습니다. pip install trl")

from core.paths import get_output_dir  # type: ignore  # noqa: E402
from training.shared.competency_extract import get_competency_sft_dir  # type: ignore  # noqa: E402


MODEL_ID = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"
# Transformers v5용 config(RopeParameters) 이전 리비전 고정 → transformers 4.x 호환
MODEL_REVISION = "0ff6b5e"
INPUT_FILE = "competency_qa_chat.jsonl"
OUTPUT_SUBDIR = "competency_adapters"
MAX_SEQ_LENGTH = 1024


def _load_jsonl(path: Path) -> list[dict]:
    """JSONL 파일 로드."""
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


def _load_and_split_data(sft_dir: Path, val_ratio: float = 0.1, seed: int = 42) -> tuple[Dataset, Dataset]:
    """competency_qa_chat.jsonl 로드 후 train/val 분할.
    train.jsonl, val.jsonl이 이미 있으면 덮어쓰지 않고 로드. 없으면 분할 후 생성."""
    in_path = sft_dir / INPUT_FILE
    train_path = sft_dir / "train.jsonl"
    val_path = sft_dir / "val.jsonl"

    if not in_path.exists():
        raise FileNotFoundError(f"파일 없음: {in_path}\n먼저 run_qa_to_chat_format.py를 실행하세요.")

    # 이미 train/val이 있으면 그대로 사용 (덮어쓰지 않음)
    if train_path.exists() and val_path.exists():
        train_rows = _load_jsonl(train_path)
        val_rows = _load_jsonl(val_path)
        if train_rows and val_rows:
            print(f"[OK] 기존 파일 사용: Train {len(train_rows)}건, Val {len(val_rows)}건 (덮어쓰지 않음)")
            return Dataset.from_list(train_rows), Dataset.from_list(val_rows)

    # 분할 후 생성
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

    # 군집 균형 분할: cluster_id 기준 stratify
    cluster_ids = [r.get("cluster_id", -1) for r in rows]
    try:
        train_rows, val_rows = train_test_split(
            rows, test_size=val_ratio, random_state=seed, stratify=cluster_ids
        )
    except ValueError:
        train_rows, val_rows = train_test_split(rows, test_size=val_ratio, random_state=seed)
    for path, data in [(train_path, train_rows), (val_path, val_rows)]:
        with path.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[OK] Train {len(train_rows)}건, Val {len(val_rows)}건 → {train_path.name}, {val_path.name} 생성")
    return Dataset.from_list(train_rows), Dataset.from_list(val_rows)


def main() -> None:
    if SFTTrainer is None:
        sys.exit(1)

    if not torch.cuda.is_available():
        print("[ERROR] CUDA가 필요합니다. GPU를 확인하세요.")
        sys.exit(1)

    print("=" * 60)
    print("[INFO] 역량 EXAONE SFT 학습 시작")
    print("=" * 60)

    sft_dir = get_competency_sft_dir()
    output_dir = get_output_dir() / "exaone" / OUTPUT_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 데이터 로드 및 분할
    print("\n[Step 1] 데이터 로드 및 train/val 분할")
    train_dataset, val_dataset = _load_and_split_data(sft_dir)

    # 2. 토크나이저 로드
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

    # 3. 모델 로드 (4-bit + LoRA)
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

    # 4. formatting_func: messages → apply_chat_template 텍스트
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

    # 5. SFTTrainer 설정 및 학습 (TRL 0.24: SFTConfig + processing_class)
    print("\n[Step 4] SFT 학습 실행")
    if SFTConfig is None:
        raise ImportError("SFTConfig를 불러올 수 없습니다. trl 버전을 확인하세요.")

    sft_config = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=4,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_steps=50,
        logging_steps=25,
        eval_steps=200,
        save_steps=200,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=False,
        bf16=torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        eval_strategy="steps",
        save_strategy="steps",
        logging_dir=str(output_dir / "logs"),
        remove_unused_columns=False,
        dataloader_num_workers=0,
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
    )

    trainer_stats = trainer.train()

    # 학습 통계 출력
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
        if m.get("num_train_epochs") is not None and m.get("train_samples_per_second") is None:
            print(f"  - 학습 에포크: {m['num_train_epochs']}")
        print()

    # 6. 저장
    print("\n[Step 5] 모델 저장")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[OK] 학습 완료: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
