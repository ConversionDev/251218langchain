"""
ETL Load: Prepare Training Dataset and Model

학습 준비 완료 단계.

역할: Load (적재)
1. 학습 데이터셋 로드 (train.jsonl, val.jsonl)
2. EXAONE 모델 및 토크나이저 로드
3. QLoRA 설정 및 모델 준비
4. 데이터셋을 모델 입력 형태로 변환
5. 학습 준비 완료

입력: transform_jsonl.py가 생성한 train.jsonl, val.jsonl
출력: 학습 준비 완료된 모델 및 데이터셋
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# EXAONE 모델의 커스텀 코드 실행을 허용
os.environ["TRANSFORMERS_TRUST_REMOTE_CODE"] = "true"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import torch
from datasets import Dataset
from peft import (
    LoraConfig,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
)

try:
    from trl import SFTTrainer
except ImportError:
    print("[WARNING] trl이 설치되지 않았습니다. SFTTrainer를 사용할 수 없습니다.")
    SFTTrainer = None


class TrainingDataLoader:
    """학습 데이터 및 모델 로더."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        device_map: str = "cuda:0",
    ):
        """초기화.

        Args:
            model_path: EXAONE 모델 경로 (None이면 자동 탐지)
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            target_modules: LoRA를 적용할 모듈 목록 (None이면 자동 감지)
            device_map: 디바이스 매핑 (기본값: "cuda:0", GPU 필수)
        """
        self.model_path = model_path or self._find_exaone_model()
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules
        self.device_map = device_map

        # QLoRA 설정 (4-bit quantization)
        self.bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        # LoRA 설정
        if target_modules is None:
            # EXAONE 모델의 attention 모듈 (일반적으로 사용되는 이름)
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

        self.lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules,
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        # 모델 및 토크나이저
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[Any] = None
        self.peft_model: Optional[Any] = None

        # 데이터셋
        self.train_dataset: Optional[Dataset] = None
        self.val_dataset: Optional[Dataset] = None

    def _find_exaone_model(self) -> Optional[str]:
        """EXAONE 모델 경로 자동 탐지.

        Returns:
            모델 경로 또는 None
        """
        # 환경 변수 확인
        env_path = os.environ.get("EXAONE_MODEL_DIR")
        if env_path:
            env_path_obj = Path(env_path)
            if env_path_obj.exists() and (env_path_obj / "config.json").exists():
                return str(env_path_obj)

        # app/artifacts/base_models/exaone 경로 확인
        app_dir = Path(__file__).parent.parent  # training -> app
        exaone_dir = app_dir / "artifacts" / "base_models" / "exaone"

        if exaone_dir.exists() and (exaone_dir / "config.json").exists():
            return str(exaone_dir)

        return None

    def load_datasets(
        self,
        train_path: Path,
        val_path: Path,
    ) -> Tuple[Dataset, Dataset]:
        """학습 데이터셋 로드.

        Args:
            train_path: train.jsonl 파일 경로
            val_path: val.jsonl 파일 경로

        Returns:
            (train_dataset, val_dataset)
        """
        print("[INFO] 데이터셋 로드 중...")

        # JSONL 파일을 Dataset으로 변환
        def load_jsonl_to_dataset(file_path: Path) -> Dataset:
            """JSONL 파일을 HuggingFace Dataset으로 변환."""
            data = []
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        data.append(item)
                    except json.JSONDecodeError:
                        continue
            return Dataset.from_list(data)

        train_dataset = load_jsonl_to_dataset(train_path)
        val_dataset = load_jsonl_to_dataset(val_path)

        print(f"[OK] Train 데이터셋: {len(train_dataset)}개 샘플")
        print(f"[OK] Validation 데이터셋: {len(val_dataset)}개 샘플")

        self.train_dataset = train_dataset
        self.val_dataset = val_dataset

        return train_dataset, val_dataset

    def load_model(self) -> Tuple[Any, AutoTokenizer]:
        """EXAONE 모델 및 토크나이저 로드.

        Returns:
            (model, tokenizer)
        """
        if self.model_path is None:
            raise ValueError(
                "EXAONE 모델 경로를 찾을 수 없습니다. "
                "app/artifacts/base_models/exaone 디렉토리에 모델 파일이 있는지 확인하거나 "
                "EXAONE_MODEL_DIR 환경 변수를 설정하세요."
            )

        print(f"[INFO] 모델 로딩 중: {self.model_path}")

        # 토크나이저 로드
        # trl >= 0.8.0에서는 max_seq_length를 여기서 설정
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            model_max_length=2048,  # max_seq_length는 여기서 설정
        )

        # pad_token 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id

        self.tokenizer = tokenizer

        # 모델 로드 (4-bit quantization)
        # QLoRA는 device_map이 딕셔너리 형태이거나 "auto"를 권장하지만,
        # GPU만 사용하려면 "cuda:0" 형식 사용
        device_map_value = self.device_map if self.device_map != "cuda" else "cuda:0"
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            quantization_config=self.bnb_config,
            device_map=device_map_value,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )

        # PEFT 모델 준비
        model = prepare_model_for_kbit_training(model)

        # LoRA 적용
        peft_model = get_peft_model(model, self.lora_config)
        peft_model.print_trainable_parameters()

        self.model = model
        self.peft_model = peft_model

        print("[OK] 모델 로딩 완료")

        return model, tokenizer

    def format_dataset(
        self,
        dataset: Dataset,
        max_seq_length: int = 2048,
    ) -> Dataset:
        """데이터셋을 모델 입력 형태로 포맷팅.

        Args:
            dataset: SFT 형식 데이터셋
            max_seq_length: 최대 시퀀스 길이

        Returns:
            포맷팅된 데이터셋
        """
        if self.tokenizer is None:
            raise ValueError("먼저 load_model()을 호출하여 토크나이저를 로드하세요.")

        def format_prompt(example: Dict[str, Any]) -> Dict[str, Any]:
            """SFT 형식을 프롬프트 문자열로 변환."""
            instruction = example.get("instruction", "")
            input_data = example.get("input", {})
            output_data = example.get("output", {})

            # 입력 구성
            subject = input_data.get("subject", "")
            attachments = input_data.get("attachments", [])
            received_at = input_data.get("received_at", "")

            attachments_str = ", ".join(attachments) if attachments else "없음"

            # 프롬프트 구성
            prompt = f"{instruction}\n\n제목: {subject}\n첨부파일: {attachments_str}\n수신일시: {received_at}"

            # 출력 구성
            action = output_data.get("action", "")
            reason = output_data.get("reason", "")
            confidence = output_data.get("confidence", 0.0)

            output_text = f'{{"action": "{action}", "reason": "{reason}", "confidence": {confidence}}}'

            # 전체 텍스트 (instruction + input + output)
            text = f"{prompt}\n\n{output_text}"

            return {"text": text}

        # 데이터셋 포맷팅
        formatted_dataset = dataset.map(
            format_prompt,
            remove_columns=dataset.column_names,
        )

        # 토크나이징
        def tokenize_function(examples: Dict[str, List[str]]) -> Dict[str, Any]:
            """텍스트를 토큰화."""
            if self.tokenizer is None:
                raise ValueError("토크나이저가 로드되지 않았습니다.")
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_seq_length,
                padding=False,
            )

        tokenized_dataset = formatted_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=formatted_dataset.column_names,
        )

        return tokenized_dataset

    def prepare_training(
        self,
        train_path: Path,
        val_path: Path,
        max_seq_length: int = 2048,
    ) -> Dict[str, Any]:
        """학습 준비 완료.

        Args:
            train_path: train.jsonl 파일 경로
            val_path: val.jsonl 파일 경로
            max_seq_length: 최대 시퀀스 길이

        Returns:
            학습 준비 완료된 객체들 (model, tokenizer, train_dataset, val_dataset)
        """
        print("=" * 60)
        print("[INFO] ETL Load 단계 시작")
        print("=" * 60)
        print()

        # 1. 데이터셋 로드
        print("[Step 1] 데이터셋 로드 중...")
        train_dataset, val_dataset = self.load_datasets(train_path, val_path)
        print()

        # 2. 모델 로드
        print("[Step 2] 모델 및 토크나이저 로드 중...")
        model, tokenizer = self.load_model()
        print()

        # 3. 데이터셋 포맷팅
        print("[Step 3] 데이터셋 포맷팅 중...")
        formatted_train = self.format_dataset(train_dataset, max_seq_length)
        formatted_val = self.format_dataset(val_dataset, max_seq_length)
        print(
            f"[OK] 포맷팅 완료: Train {len(formatted_train)}개, Val {len(formatted_val)}개"
        )
        print()

        # 4. DataCollator 설정
        print("[Step 4] DataCollator 설정 중...")
        if tokenizer is None:
            raise ValueError("토크나이저가 로드되지 않았습니다.")
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,  # Causal LM이므로 False
        )
        print("[OK] DataCollator 설정 완료")
        print()

        print("=" * 60)
        print("[OK] ETL Load 단계 완료!")
        print("=" * 60)
        print("[INFO] 학습 준비 완료:")
        print(f"  - 모델: {self.model_path}")
        print(f"  - Train 샘플: {len(formatted_train)}개")
        print(f"  - Validation 샘플: {len(formatted_val)}개")
        print(f"  - 최대 시퀀스 길이: {max_seq_length}")
        print()

        return {
            "model": self.peft_model,
            "tokenizer": tokenizer,
            "train_dataset": formatted_train,
            "val_dataset": formatted_val,
            "data_collator": data_collator,
            "lora_config": self.lora_config,
        }


def main():
    """메인 실행 함수."""
    # 경로 설정
    current_dir = Path(__file__).parent.parent.parent  # spam_agent -> service -> api
    data_dir = current_dir / "data" / "sft_dataset" / "processed"

    # 입력 파일
    train_path = data_dir / "train.jsonl"
    val_path = data_dir / "val.jsonl"

    # 파일 존재 확인
    if not train_path.exists():
        print(f"[ERROR] Train 파일을 찾을 수 없습니다: {train_path}")
        print(
            "[INFO] 먼저 transform_jsonl.py를 실행하여 train.jsonl 파일을 생성하세요."
        )
        return

    if not val_path.exists():
        print(f"[ERROR] Validation 파일을 찾을 수 없습니다: {val_path}")
        print("[INFO] 먼저 transform_jsonl.py를 실행하여 val.jsonl 파일을 생성하세요.")
        return

    # TrainingDataLoader 생성
    loader = TrainingDataLoader(
        model_path=None,  # 자동 탐지
        lora_r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        device_map="cuda:0",
    )

    # 학습 준비
    try:
        training_objects = loader.prepare_training(
            train_path=train_path,
            val_path=val_path,
            max_seq_length=2048,
        )

        print("[OK] 학습 준비 완료!")
        print("[INFO] 다음 단계: SFTTrainer를 사용하여 학습을 시작하세요.")
        print()
        print("[INFO] 사용 예시:")
        print("  from trl import SFTTrainer")
        print("  from transformers import TrainingArguments")
        print()
        print("  trainer = SFTTrainer(")
        print("      model=training_objects['model'],")
        print("      train_dataset=training_objects['train_dataset'],")
        print("      eval_dataset=training_objects['val_dataset'],")
        print("      tokenizer=training_objects['tokenizer'],")
        print("      data_collator=training_objects['data_collator'],")
        print("      args=TrainingArguments(...),")
        print("  )")
        print("  trainer.train()")
        print()
        print(f"[INFO] 학습 준비 완료된 객체: {list(training_objects.keys())}")

    except Exception as e:
        print(f"[ERROR] 학습 준비 실패: {e}")
        import traceback

        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
