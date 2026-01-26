"""
LoRA Adapter Training with SFTTrainer

PEFT/LoRA 기반 파인튜닝 학습 실행.

역할: 학습 실행
1. load_model.py에서 준비된 모델 및 데이터셋 사용
2. 하이퍼파라미터 설정 (학습률, 배치 크기, 에포크 등)
3. SFTTrainer를 사용한 학습 실행
4. LoRA 어댑터 저장

입력: load_model.py가 준비한 모델 및 데이터셋
출력: 학습된 LoRA 어댑터 (체크포인트)
"""

import os
import sys
from pathlib import Path

# app/ 디렉토리를 Python 경로에 추가
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# EXAONE 모델의 커스텀 코드 실행을 허용
# SFTTrainer 내부에서 AutoProcessor 호출 시 필요
os.environ["TRANSFORMERS_TRUST_REMOTE_CODE"] = "true"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Unsloth SFTTrainer 패치 방지 (EXAONE은 Unsloth와 호환되지 않음)
# 이 환경 변수를 설정하면 Unsloth가 SFTTrainer를 패치하지 않음
os.environ["UNSLOTH_DISABLE_TRAINER_PATCH"] = "1"

from typing import Any, Dict, Optional

from transformers import TrainingArguments

# trl 버전에 따라 import 방식이 다름
# 중요: Unsloth가 이미 import된 경우에도 원본 SFTTrainer를 사용하도록 함
SFTTrainer = None
SFTConfig = None

# Unsloth 패치 전에 원본 SFTTrainer를 가져오기 위해 직접 import
try:
    # trl의 원본 SFTTrainer 직접 import
    from trl.trainer.sft_trainer import SFTTrainer as _OriginalSFTTrainer  # type: ignore
    SFTTrainer = _OriginalSFTTrainer
    try:
        from trl import SFTConfig  # type: ignore
    except ImportError:
        try:
            from trl.trainer.sft_config import SFTConfig  # type: ignore
        except ImportError:
            SFTConfig = None
    print("[INFO] EXAONE 학습: 원본 TRL SFTTrainer 사용 (Unsloth 패치 비활성화)")
except ImportError:
    try:
        from trl import SFTConfig, SFTTrainer  # type: ignore
    except ImportError:
        try:
            from trl import SFTTrainer  # type: ignore
        except ImportError:
            print("[ERROR] trl이 설치되지 않았습니다. pip install trl을 실행하세요.")

from training.load_model import TrainingDataLoader  # type: ignore


class LoRATrainer:
    """LoRA 어댑터 학습 클래스."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        device_map: str = "cuda:0",
    ):
        """초기화.

        Args:
            output_dir: 학습 결과 저장 디렉토리 (None이면 자동 생성)
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            device_map: 디바이스 매핑 (기본값: "cuda:0", GPU 필수)
        """
        # 출력 디렉토리 설정
        if output_dir is None:
            from domain.v1.spam.services.utils import get_output_dir  # type: ignore

            output_dir_path = get_output_dir() / "exaone" / "adapters"
        else:
            output_dir_path = Path(output_dir)

        self.output_dir = output_dir_path
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # TrainingDataLoader 생성 (EXAONE은 Unsloth 비활성화)
        self.data_loader = TrainingDataLoader(
            model_path=None,  # 자동 탐지
            lora_r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            device_map=device_map,
            use_unsloth=False,  # EXAONE은 Unsloth와 호환되지 않음
        )

        # 학습 객체
        self.training_objects: Optional[Dict[str, Any]] = None
        self.trainer: Optional[Any] = None

    def _create_sft_trainer(
        self,
        trainer_kwargs: Dict[str, Any],
    ) -> Any:
        """SFTTrainer 생성 (trl >= 0.8.0 기준).

        trl >= 0.8.0 핵심 변화:
        - max_seq_length는 SFTTrainer에서 제거됨 (tokenizer.model_max_length로 설정)
        - tokenizer → processing_class로 변경됨
        - trust_remote_code=True 필수

        Args:
            trainer_kwargs: SFTTrainer에 전달할 파라미터

        Returns:
            SFTTrainer 인스턴스
        """
        if self.training_objects is None:
            raise ValueError(
                "training_objects가 None입니다. prepare_training_data()를 먼저 호출하세요."
            )

        tokenizer = self.training_objects.get("tokenizer")

        # 제거된 파라미터 정리
        trainer_kwargs.pop("max_seq_length", None)
        trainer_kwargs.pop("packing", None)
        trainer_kwargs.pop("data_collator", None)
        trainer_kwargs.pop("tokenizer", None)

        # trl >= 0.8.0: processing_class 사용
        trainer_kwargs["processing_class"] = tokenizer
        trainer_kwargs["trust_remote_code"] = True

        try:
            return SFTTrainer(**trainer_kwargs)  # type: ignore
        except TypeError as e:
            error_msg = str(e)
            print(f"[DEBUG] 시도 1 실패 (processing_class): {error_msg}")

            # processing_class가 지원되지 않는 경우 → tokenizer 시도
            if "processing_class" in error_msg:
                print("[INFO] tokenizer 파라미터로 재시도...")
                trainer_kwargs.pop("processing_class", None)
                trainer_kwargs["tokenizer"] = tokenizer
                try:
                    return SFTTrainer(**trainer_kwargs)  # type: ignore
                except TypeError as e2:
                    error_msg2 = str(e2)
                    print(f"[DEBUG] 시도 2 실패 (tokenizer): {error_msg2}")

                    # tokenizer도 안되면 trust_remote_code 제거
                    if "tokenizer" in error_msg2:
                        trainer_kwargs.pop("tokenizer", None)
                    if "trust_remote_code" in error_msg2:
                        trainer_kwargs.pop("trust_remote_code", None)
                    try:
                        return SFTTrainer(**trainer_kwargs)  # type: ignore
                    except TypeError as e3:
                        print(f"[DEBUG] 시도 3 실패: {e3}")
                        raise

            # trust_remote_code가 안되는 경우
            if "trust_remote_code" in error_msg:
                print("[INFO] trust_remote_code 제거 후 재시도...")
                trainer_kwargs.pop("trust_remote_code", None)
                try:
                    return SFTTrainer(**trainer_kwargs)  # type: ignore
                except TypeError as e2:
                    print(f"[ERROR] 재시도 실패: {e2}")
                    raise

            raise RuntimeError(f"SFTTrainer 생성 실패.\n오류: {error_msg}")

    def prepare_training_data(
        self,
        train_path: Optional[Path] = None,
        val_path: Optional[Path] = None,
        max_seq_length: int = 2048,
    ) -> Dict[str, Any]:
        """학습 데이터 준비.

        Args:
            train_path: train.jsonl 파일 경로 (None이면 자동 탐지)
            val_path: val.jsonl 파일 경로 (None이면 자동 탐지)
            max_seq_length: 최대 시퀀스 길이

        Returns:
            학습 준비 완료된 객체들
        """
        # 경로 자동 탐지
        if train_path is None or val_path is None:
            current_dir = Path(
                __file__
            ).parent.parent.parent  # spam_agent -> service -> api
            data_dir = current_dir / "data" / "sft_dataset" / "processed"

            if train_path is None:
                train_path = data_dir / "train.jsonl"
            if val_path is None:
                val_path = data_dir / "val.jsonl"

        # 파일 존재 확인
        if not train_path.exists():
            raise FileNotFoundError(
                f"Train 파일을 찾을 수 없습니다: {train_path}\n"
                "먼저 transform_jsonl.py를 실행하여 train.jsonl 파일을 생성하세요."
            )

        if not val_path.exists():
            raise FileNotFoundError(
                f"Validation 파일을 찾을 수 없습니다: {val_path}\n"
                "먼저 transform_jsonl.py를 실행하여 val.jsonl 파일을 생성하세요."
            )

        # 학습 준비
        self.training_objects = self.data_loader.prepare_training(
            train_path=train_path,
            val_path=val_path,
            max_seq_length=max_seq_length,
        )

        if self.training_objects is None:
            raise ValueError("학습 데이터 준비에 실패했습니다.")
        return self.training_objects

    def train(
        self,
        num_epochs: int = 2,
        per_device_train_batch_size: int = 8,  # 4 → 8 (속도 향상)
        per_device_eval_batch_size: int = 4,  # 2 → 4 (속도 향상)
        gradient_accumulation_steps: int = 1,  # 2 → 1 (속도 향상)
        learning_rate: float = 2e-4,
        warmup_steps: int = 50,  # 100 → 50 (속도 향상)
        logging_steps: int = 25,  # 50 → 25
        eval_steps: int = 500,  # 1000 → 500
        save_steps: int = 500,  # 1000 → 500
        save_total_limit: int = 3,
        load_best_model_at_end: bool = True,
        metric_for_best_model: str = "eval_loss",
        greater_is_better: bool = False,
        max_seq_length: int = 512,
        fp16: bool = False,
        bf16: bool = True,
        optim: str = "paged_adamw_8bit",
        lr_scheduler_type: str = "cosine",
        report_to: Optional[str] = None,
        dataloader_num_workers: int = 0,  # 4 → 0 (Windows 멀티프로세싱 오버헤드 제거)
        gradient_checkpointing: bool = False,  # True → False (속도 향상, 메모리 사용량 증가)
    ) -> Path:
        """SFT 학습 실행.

        Args:
            num_epochs: 학습 에포크 수
            per_device_train_batch_size: 디바이스당 학습 배치 크기
            per_device_eval_batch_size: 디바이스당 평가 배치 크기
            gradient_accumulation_steps: 그래디언트 누적 스텝
            learning_rate: 학습률
            warmup_steps: 워밍업 스텝 수
            logging_steps: 로깅 스텝 간격
            eval_steps: 평가 스텝 간격
            save_steps: 저장 스텝 간격
            save_total_limit: 최대 체크포인트 보관 수
            load_best_model_at_end: 학습 종료 시 최적 모델 로드 여부
            metric_for_best_model: 최적 모델 선택 기준 메트릭
            greater_is_better: 메트릭이 클수록 좋은지 여부
            max_seq_length: 최대 시퀀스 길이
            fp16: FP16 사용 여부
            bf16: BF16 사용 여부
            optim: 옵티마이저 타입
            lr_scheduler_type: 학습률 스케줄러 타입
            report_to: 로깅 대상 (None이면 로깅 안 함)

        Returns:
            학습 결과 저장 디렉토리 경로
        """
        if SFTTrainer is None:
            raise ImportError(
                "trl이 설치되지 않았습니다. pip install trl을 실행하세요."
            )

        if self.training_objects is None:
            raise ValueError(
                "먼저 prepare_training_data()를 호출하여 학습 데이터를 준비하세요."
            )

        print("=" * 60)
        print("[INFO] SFT 학습 시작")
        print("=" * 60)
        print()

        # TrainingArguments 설정
        print("[Step 1] 하이퍼파라미터 설정 중...")
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            per_device_eval_batch_size=per_device_eval_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            eval_steps=eval_steps,
            save_steps=save_steps,
            save_total_limit=save_total_limit,
            load_best_model_at_end=load_best_model_at_end,
            metric_for_best_model=metric_for_best_model,
            greater_is_better=greater_is_better,
            fp16=fp16,
            bf16=bf16,
            optim=optim,
            lr_scheduler_type=lr_scheduler_type,
            report_to=report_to if report_to else [],
            eval_strategy="steps",
            save_strategy="steps",
            logging_dir=str(self.output_dir / "logs"),
            remove_unused_columns=False,
            dataloader_num_workers=dataloader_num_workers,
            gradient_checkpointing=gradient_checkpointing,
        )

        print("[OK] 하이퍼파라미터 설정 완료:")
        print(f"  - 에포크: {num_epochs}")
        print(
            f"  - 배치 크기: {per_device_train_batch_size} (누적: {gradient_accumulation_steps})"
        )
        print(f"  - 학습률: {learning_rate}")
        # max_seq_length는 tokenizer.model_max_length로 설정됨 (trl >= 0.8.0)
        print(f"  - 최대 시퀀스 길이: {max_seq_length} (tokenizer에 설정됨)")
        print()

        # SFTTrainer 생성
        print("[Step 2] SFTTrainer 설정 중...")

        # trl >= 0.8.0 기준 파라미터
        trainer_kwargs: Dict[str, Any] = {
            "model": self.training_objects["model"],
            "train_dataset": self.training_objects["train_dataset"],
            "eval_dataset": self.training_objects["val_dataset"],
            "args": training_args,
        }

        # SFTTrainer 생성 (trl >= 0.8.0 기준)
        trainer = self._create_sft_trainer(trainer_kwargs)

        self.trainer = trainer
        print("[OK] SFTTrainer 설정 완료")
        print()

        # 학습 실행
        print("[Step 3] 학습 실행 중...")
        print(f"[INFO] 출력 디렉토리: {self.output_dir}")
        print()

        try:
            train_result = trainer.train()
            print()
            print("[OK] 학습 완료!")
            print(f"[INFO] 학습 손실: {train_result.training_loss:.4f}")
            if hasattr(train_result, "metrics"):
                print(f"[INFO] 학습 메트릭: {train_result.metrics}")
            print()
        except Exception as e:
            print(f"[ERROR] 학습 중 오류 발생: {e}")
            import traceback

            traceback.print_exc()
            raise

        # 최종 모델 저장
        print("[Step 4] LoRA 어댑터 저장 중...")
        trainer.save_model()
        self.training_objects["tokenizer"].save_pretrained(str(self.output_dir))

        print(f"[OK] LoRA 어댑터 저장 완료: {self.output_dir}")
        print()

        # 학습 정보 저장
        self._save_training_info(training_args, train_result)

        return self.output_dir

    def _save_training_info(
        self, training_args: TrainingArguments, train_result: Any
    ) -> None:
        """학습 정보를 파일로 저장.

        Args:
            training_args: 학습 인자
            train_result: 학습 결과
        """
        info_file = self.output_dir / "training_info.txt"

        with info_file.open("w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("학습 정보\n")
            f.write("=" * 60 + "\n\n")

            f.write("하이퍼파라미터:\n")
            f.write(f"  - 에포크: {training_args.num_train_epochs}\n")
            f.write(f"  - 배치 크기: {training_args.per_device_train_batch_size}\n")
            f.write(
                f"  - 그래디언트 누적: {training_args.gradient_accumulation_steps}\n"
            )
            f.write(f"  - 학습률: {training_args.learning_rate}\n")
            f.write(f"  - 워밍업 스텝: {training_args.warmup_steps}\n")
            f.write(f"  - 옵티마이저: {training_args.optim}\n")
            f.write(f"  - 스케줄러: {training_args.lr_scheduler_type}\n")
            f.write("\n")

            f.write("LoRA 설정:\n")
            f.write(f"  - LoRA rank (r): {self.data_loader.lora_r}\n")
            f.write(f"  - LoRA alpha: {self.data_loader.lora_alpha}\n")
            f.write(f"  - LoRA dropout: {self.data_loader.lora_dropout}\n")
            f.write(f"  - Target modules: {self.data_loader.target_modules}\n")
            f.write("\n")

            f.write("학습 결과:\n")
            f.write(f"  - 학습 손실: {train_result.training_loss:.4f}\n")
            if hasattr(train_result, "metrics"):
                for key, value in train_result.metrics.items():
                    f.write(f"  - {key}: {value}\n")
            f.write("\n")

            f.write("모델 정보:\n")
            f.write(f"  - 모델 경로: {self.data_loader.model_path}\n")
            f.write(f"  - 출력 경로: {self.output_dir}\n")
            f.write("\n")

        print(f"[OK] 학습 정보 저장: {info_file}")


def main():
    """메인 실행 함수."""
    print("=" * 60)
    print("[INFO] LoRA 어댑터 학습 시작")
    print("=" * 60)
    print()

    # LoRATrainer 생성
    trainer = LoRATrainer(
        output_dir=None,  # 자동 생성
        lora_r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        device_map="cuda:0",
    )

    try:
        # 학습 데이터 준비
        print("[INFO] 학습 데이터 준비 중...")
        trainer.prepare_training_data(
            train_path=None,  # 자동 탐지
            val_path=None,  # 자동 탐지
            max_seq_length=2048,
        )
        print()

        # 학습 실행 (최적화된 설정)
        output_dir = trainer.train(
            num_epochs=2,  # 최적화: 3 → 2
            per_device_train_batch_size=4,  # 최적화: 1 → 4
            per_device_eval_batch_size=2,  # 최적화: 1 → 2
            gradient_accumulation_steps=2,  # 최적화: 8 → 2 (실제 배치 = 8 유지)
            learning_rate=2e-4,
            warmup_steps=100,
            logging_steps=50,  # 최적화: 10 → 50
            eval_steps=1000,  # 최적화: 500 → 1000
            save_steps=1000,  # 최적화: 500 → 1000
            save_total_limit=3,
            load_best_model_at_end=True,
            max_seq_length=512,  # 최적화: 2048 → 512
            fp16=False,
            bf16=True,
            optim="paged_adamw_8bit",
            lr_scheduler_type="cosine",
            dataloader_num_workers=4,  # 최적화 추가
            gradient_checkpointing=True,  # 최적화 추가
        )

        print("=" * 60)
        print("[OK] 학습 완료!")
        print("=" * 60)
        print(f"[INFO] LoRA 어댑터 저장 위치: {output_dir}")
        print()
        print("[INFO] 다음 단계:")
        print("  1. 학습된 어댑터를 사용하여 추론 테스트")
        print("  2. 성능 평가 및 개선")
        print("  3. 필요시 추가 학습 및 하이퍼파라미터 조정")

    except Exception as e:
        print(f"[ERROR] 학습 실패: {e}")
        import traceback

        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
