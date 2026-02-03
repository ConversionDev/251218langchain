"""
ETL Load: Prepare Training Dataset and Model

학습 준비 완료 단계.

역할: Load (적재)
1. 학습 데이터셋 로드 (train.jsonl, val.jsonl)
2. EXAONE 모델 및 토크나이저 로드
3. QLoRA 설정 및 모델 준비
4. 데이터셋을 모델 입력 형태로 변환
5. 학습 준비 완료

입력: sft_to_train_val_split.py가 생성한 train.jsonl, val.jsonl
출력: 학습 준비 완료된 모델 및 데이터셋
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# EXAONE 모델의 커스텀 코드 실행을 허용
os.environ["TRANSFORMERS_TRUST_REMOTE_CODE"] = "true"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Unsloth 캐시 설정 (리소스 매니저에서 관리)
from core.resource_manager import setup_unsloth_cache  # type: ignore # noqa: E402

setup_unsloth_cache()

# EXAONE은 Unsloth와 호환되지 않음 (causal_mask 파라미터 문제)
# 따라서 이 모듈에서는 Unsloth를 사용하지 않음
_UNSLOTH_AVAILABLE = False
FastLanguageModel = None  # type: ignore
print("[INFO] EXAONE 학습: Unsloth 비활성화 (호환성 문제로 transformers + TRL + PEFT 사용)")

import torch  # noqa: E402
from datasets import Dataset  # noqa: E402
from peft import (  # noqa: E402
    LoraConfig,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from transformers import (  # noqa: E402
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
)

# HuggingFace 캐시 확인을 위한 import
try:
    from huggingface_hub import scan_cache_dir  # noqa: E402
    _HF_HUB_AVAILABLE = True
except ImportError:
    _HF_HUB_AVAILABLE = False
    scan_cache_dir = None  # type: ignore

try:
    from trl import SFTTrainer
except ImportError:
    print("[WARNING] trl이 설치되지 않았습니다. SFTTrainer를 사용할 수 없습니다.")
    SFTTrainer = None


class TrainingDataLoader:
    """학습 데이터 및 모델 로더."""

    # 클래스 변수: 로컬 경로 존재 여부 캐싱 (파일 시스템 체크 최적화)
    _local_exaone_path_cache: Optional[str] = None
    _local_exaone_path_checked: bool = False

    # 클래스 변수: GPU 정보 캐싱 (GPU 확인 최적화)
    _gpu_name_cache: Optional[str] = None
    _gpu_memory_cache: Optional[float] = None

    # 클래스 변수: HuggingFace 캐시 확인 결과 캐싱
    _hf_cache_checked: Dict[str, bool] = {}

    def __init__(
        self,
        model_path: Optional[str] = None,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        device_map: str = "cuda:0",
        use_unsloth: bool = False,  # EXAONE은 Unsloth와 호환되지 않음 (항상 False)
    ):
        """초기화.

        Args:
            model_path: EXAONE 모델 경로 (None이면 자동 탐지)
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            target_modules: LoRA를 적용할 모듈 목록 (None이면 자동 감지)
            device_map: 디바이스 매핑 (기본값: "cuda:0", GPU 필수)
            use_unsloth: 무시됨 (EXAONE은 Unsloth와 호환되지 않아 항상 비활성화)
        """
        self.model_path = model_path or self._find_exaone_model()
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules
        self.device_map = device_map

        # EXAONE 모델은 Unsloth와 호환되지 않음 (causal_mask 파라미터 문제)
        # 이 모듈은 EXAONE 전용이므로 항상 Unsloth 비활성화
        self.use_unsloth = False
        print("[INFO] EXAONE 모델: transformers + TRL + PEFT 사용 (Unsloth 비활성화)")

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

    def _find_exaone_model(self) -> str:
        """EXAONE 모델 경로 또는 HuggingFace 모델 ID 자동 탐지.

        우선순위:
        1. 환경 변수 EXAONE_MODEL_DIR
        2. app/artifacts/base_models/exaone (로컬 경로, 캐싱됨)
        3. HuggingFace 모델 ID (캐시에서 자동 로드)

        Returns:
            모델 경로 또는 HuggingFace 모델 ID
        """
        # 1. 환경 변수 확인 (최우선, 빠른 체크)
        env_path = os.environ.get("EXAONE_MODEL_DIR")
        if env_path:
            env_path_obj = Path(env_path)
            # 환경 변수 경로는 매번 체크 (사용자가 변경할 수 있음)
            if env_path_obj.exists() and (env_path_obj / "config.json").exists():
                print(f"[INFO] 환경 변수에서 EXAONE 모델 경로 사용: {env_path}")
                return str(env_path_obj)

        # 2. 로컬 경로 확인 (캐싱으로 최적화)
        # 클래스 변수로 한 번만 체크하고 결과 재사용
        if not TrainingDataLoader._local_exaone_path_checked:
            app_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            exaone_dir = app_dir / "artifacts" / "base_models" / "exaone"

            # 파일 시스템 체크는 한 번만 수행
            if exaone_dir.exists() and (exaone_dir / "config.json").exists():
                TrainingDataLoader._local_exaone_path_cache = str(exaone_dir)
            else:
                TrainingDataLoader._local_exaone_path_cache = None

            TrainingDataLoader._local_exaone_path_checked = True

        # 캐시된 결과 사용
        if TrainingDataLoader._local_exaone_path_cache:
            print(f"[INFO] 로컬 경로에서 EXAONE 모델 사용: {TrainingDataLoader._local_exaone_path_cache}")
            return TrainingDataLoader._local_exaone_path_cache

        # 3. HuggingFace 모델 ID 반환 (캐시에서 자동 로드)
        # 로컬 경로가 없으면 바로 반환 (추가 파일 시스템 체크 없음)
        default_model_id = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"

        # HuggingFace 캐시 사전 확인 (한 번만 확인하고 캐싱)
        if default_model_id not in TrainingDataLoader._hf_cache_checked:
            cache_exists = self._check_hf_cache(default_model_id)
            TrainingDataLoader._hf_cache_checked[default_model_id] = cache_exists

        cache_status = TrainingDataLoader._hf_cache_checked[default_model_id]
        if cache_status:
            print(f"[INFO] 로컬 경로가 없어 HuggingFace 모델 ID 사용: {default_model_id}")
            print("[INFO] HuggingFace 캐시에서 모델을 로드합니다.")
        else:
            print(f"[INFO] 로컬 경로가 없어 HuggingFace 모델 ID 사용: {default_model_id}")
            print("[WARNING] HuggingFace 캐시에 모델이 없습니다. 다운로드가 시작됩니다.")
            print("[INFO] 첫 다운로드는 시간이 걸릴 수 있습니다.")

        return default_model_id

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

    def _check_hf_cache(self, model_id: str) -> bool:
        """HuggingFace 캐시에 모델이 있는지 확인.

        Args:
            model_id: HuggingFace 모델 ID (예: "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct")

        Returns:
            캐시에 모델이 있으면 True, 없으면 False
        """
        if not _HF_HUB_AVAILABLE or scan_cache_dir is None:
            # huggingface_hub가 없으면 확인 불가 (항상 True로 가정)
            return True

        try:
            cache_info = scan_cache_dir()
            repos = list(cache_info.repos)

            # 모델 ID로 캐시 검색
            for repo in repos:
                if repo.repo_id == model_id:
                    # 모델이 캐시에 있음
                    return True

            # 캐시에 없음
            return False
        except Exception as e:
            # 오류 발생 시 안전하게 True 반환 (다운로드 시도)
            print(f"[WARNING] HuggingFace 캐시 확인 실패: {e}")
            return True

    def load_model(self) -> Tuple[Any, AutoTokenizer]:
        """EXAONE 모델 및 토크나이저 로드.

        Returns:
            (model, tokenizer)
        """
        # GPU 필수 확인
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA가 사용 불가능합니다. GPU가 필요합니다.\n"
                "학습은 반드시 GPU 메모리를 사용해야 합니다."
            )

        # GPU 정보 캐싱 (한 번만 확인하고 재사용)
        if TrainingDataLoader._gpu_name_cache is None:
            TrainingDataLoader._gpu_name_cache = torch.cuda.get_device_name(0)
            gpu_props = torch.cuda.get_device_properties(0)
            TrainingDataLoader._gpu_memory_cache = gpu_props.total_memory / (1024**3)

        print(f"[INFO] GPU 확인: {TrainingDataLoader._gpu_name_cache}")
        print(f"[INFO] GPU 메모리: {TrainingDataLoader._gpu_memory_cache:.2f} GB")
        print()

        # model_path는 이제 항상 반환됨 (HuggingFace 모델 ID 포함)
        if not self.model_path:
            raise ValueError(
                "EXAONE 모델을 찾을 수 없습니다. "
                "다음 중 하나를 확인하세요:\n"
                "1. app/artifacts/base_models/exaone 디렉토리에 모델 파일이 있는지\n"
                "2. EXAONE_MODEL_DIR 환경 변수가 설정되어 있는지\n"
                "3. HuggingFace 캐시에 모델이 다운로드되어 있는지"
            )

        print(f"[INFO] 모델 로딩 중: {self.model_path}")
        print(f"[INFO] 디바이스: {self.device_map} (GPU 메모리 사용)")

        # EXAONE은 Unsloth와 호환되지 않으므로 항상 transformers 사용
        print("[INFO] transformers + PEFT로 EXAONE 모델 로딩 중...")

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

        # HuggingFace 모델 ID인 경우 캐시 확인 (이미 _find_exaone_model에서 확인됨)
        if "/" in str(self.model_path) and not Path(self.model_path).exists():
            model_id = str(self.model_path)
            if model_id in TrainingDataLoader._hf_cache_checked:
                cache_exists = TrainingDataLoader._hf_cache_checked[model_id]
                if cache_exists:
                    print("[INFO] HuggingFace 모델 ID 감지: 캐시에서 로드 중...")
                else:
                    print("[INFO] HuggingFace 모델 ID 감지: 다운로드 중... (캐시에 없음)")

        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            quantization_config=self.bnb_config,
            device_map=device_map_value,
            trust_remote_code=True,
            dtype=torch.bfloat16,
        )

        # PEFT 모델 준비 (중간 모델 객체는 자동으로 GC 처리됨)
        model = prepare_model_for_kbit_training(model)

        # LoRA 적용 (기존 model 객체는 peft_model로 대체됨)
        peft_model = get_peft_model(model, self.lora_config)
        peft_model.print_trainable_parameters()

        # GPU 사용 확인
        next_param = next(peft_model.parameters())
        device = next_param.device
        if device.type != "cuda":
            raise RuntimeError(
                f"모델이 GPU에 로드되지 않았습니다. 현재 디바이스: {device}\n"
                "학습은 반드시 GPU 메모리를 사용해야 합니다."
            )
        print(f"[OK] 모델이 GPU에 로드됨: {device}")

        # 메모리 정리: 원본 model 객체는 더 이상 필요 없음 (peft_model이 포함)
        # peft_model이 model을 포함하므로 model 참조는 제거 가능
        # 하지만 반환값과 self.model에 저장해야 하므로 유지
        self.model = model  # 원본 모델 참조 유지 (peft_model이 내부적으로 사용)
        self.peft_model = peft_model

        print("[OK] 모델 로딩 완료 (GPU 메모리 사용)")

        # peft_model 반환 (학습에 사용)
        return peft_model, tokenizer

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
    current_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    data_dir = current_dir / "data" / "sft_dataset" / "processed"

    # 입력 파일
    train_path = data_dir / "train.jsonl"
    val_path = data_dir / "val.jsonl"

    # 파일 존재 확인
    if not train_path.exists():
        print(f"[ERROR] Train 파일을 찾을 수 없습니다: {train_path}")
        print(
            "[INFO] 먼저 sft_to_train_val_split.py를 실행하여 train.jsonl 파일을 생성하세요."
        )
        return

    if not val_path.exists():
        print(f"[ERROR] Validation 파일을 찾을 수 없습니다: {val_path}")
        print("[INFO] 먼저 sft_to_train_val_split.py를 실행하여 val.jsonl 파일을 생성하세요.")
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
