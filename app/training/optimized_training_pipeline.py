"""
최적화된 학습 파이프라인

역할: 학습 시간 최소화를 위한 통합 파이프라인
1. LLaMA로 데이터 필터링
2. 최적화된 설정으로 EXAONE 학습
3. 전체 프로세스 자동화
"""

import sys
from pathlib import Path
from typing import Optional

# app/ 디렉토리를 Python 경로에 추가
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.llm.providers.llama import LLaMAGate  # type: ignore
from domain.spam.services.utils import (  # type: ignore
    get_data_dir,
    get_output_dir,
)
from training.data_filter import filter_training_data  # type: ignore
from training.lora_adapter import LoRATrainer  # type: ignore


class OptimizedTrainingPipeline:
    """최적화된 학습 파이프라인."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        use_filtered_data: bool = True,
        min_score: float = 0.35,
        max_score: float = 0.65,
        max_train_samples: int = 2000,
        max_val_samples: int = 200,
    ):
        """초기화.

        Args:
            output_dir: 출력 디렉토리 (None이면 자동 생성)
            use_filtered_data: 필터링된 데이터 사용 여부
            min_score: 최소 스팸 확률 (필터링용)
            max_score: 최대 스팸 확률 (필터링용)
            max_train_samples: 최대 학습 샘플 수
            max_val_samples: 최대 검증 샘플 수
        """
        self.use_filtered_data = use_filtered_data
        self.min_score = min_score
        self.max_score = max_score
        self.max_train_samples = max_train_samples
        self.max_val_samples = max_val_samples

        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir_path = get_output_dir() / "exaone" / "adapters"
        else:
            output_dir_path = Path(output_dir)

        self.output_dir: Path = output_dir_path
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 필터링된 데이터 저장 경로
        self.filtered_data_dir = get_data_dir() / "sft_dataset" / "filtered"

    def run(self) -> Path:
        """전체 파이프라인 실행.

        Returns:
            학습 결과 저장 디렉토리 경로
        """
        print("=" * 60)
        print("[INFO] 최적화된 학습 파이프라인 시작")
        print("=" * 60)
        print()

        # 경로 자동 탐지
        data_dir = get_data_dir() / "sft_dataset" / "processed"
        train_path = data_dir / "train.jsonl"
        val_path = data_dir / "val.jsonl"

        # Step 1: 데이터 필터링 (선택적)
        if self.use_filtered_data:
            print("[Phase 1] 데이터 필터링")
            print("-" * 60)

            # LLaMA 분류기 로드
            print("[INFO] LLaMA 분류기 로딩 중...")
            llama_gate = LLaMAGate(
                model_id="meta-llama/Llama-3.1-8B-Instruct",
                use_4bit=True,
            )
            print()

            # 필터링 실행
            filtered_train_path, filtered_val_path = filter_training_data(
                train_path=train_path,
                val_path=val_path,
                output_dir=self.filtered_data_dir,
                llama_gate=llama_gate,
                min_score=self.min_score,
                max_score=self.max_score,
                max_train_samples=self.max_train_samples,
                max_val_samples=self.max_val_samples,
                adaptive_filtering=True,  # 적응형 필터링 활성화
            )

            # 필터링된 데이터 경로 사용
            train_path = filtered_train_path
            val_path = filtered_val_path
            print()

        # Step 2: EXAONE LoRA 학습 (최적화된 설정)
        print("[Phase 2] EXAONE LoRA 학습 (최적화된 설정)")
        print("-" * 60)

        # LoRATrainer 생성
        trainer = LoRATrainer(
            output_dir=str(self.output_dir),
            lora_r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            device_map="cuda:0",
        )

        # 학습 데이터 준비
        print("[INFO] 학습 데이터 준비 중...")
        trainer.prepare_training_data(
            train_path=train_path,
            val_path=val_path,
            max_seq_length=512,  # 최적화된 시퀀스 길이
        )
        print()

        # 학습 실행 (최적화된 설정)
        print("[INFO] 최적화된 설정으로 학습 시작...")
        output_dir = Path(
            trainer.train(
                num_epochs=2,  # 최적화
                per_device_train_batch_size=4,  # 최적화
                per_device_eval_batch_size=2,  # 최적화
                gradient_accumulation_steps=2,  # 최적화
                max_seq_length=512,  # 최적화
                eval_steps=1000,  # 최적화
                save_steps=1000,  # 최적화
                logging_steps=50,  # 최적화
                dataloader_num_workers=4,  # 최적화
                gradient_checkpointing=True,  # 최적화
            )
        )

        # SFT 모델 정보 저장
        final_model_info = {
            "sft_model_path": str(output_dir),
            "is_merged": False,
        }
        import json

        info_file = output_dir / "final_model_info.json"
        with info_file.open("w", encoding="utf-8") as f:
            json.dump(final_model_info, f, indent=2, ensure_ascii=False)
        print(f"[INFO] 모델 정보 저장: {info_file}")
        print()

        print()
        print("=" * 60)
        print("[OK] 최적화된 학습 파이프라인 완료!")
        print("=" * 60)
        print(f"[INFO] 학습 결과 저장 위치: {output_dir}")
        print()
        print("=" * 60)
        print("[INFO] 다음 단계")
        print("=" * 60)
        print("  1. SFT 모델 평가 (test_lora.py 사용)")
        print("  2. 평가 결과 확인")
        print("  3. 필요시 추가 학습 및 하이퍼파라미터 조정")
        print("=" * 60)
        print()

        return output_dir


def main():
    """메인 실행 함수."""
    import argparse

    parser = argparse.ArgumentParser(description="최적화된 학습 파이프라인")
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="출력 디렉토리 (None이면 자동 생성)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="데이터 필터링 건너뛰기 (전체 데이터 사용)",
    )
    parser.add_argument(
        "--min_score",
        type=float,
        default=0.35,
        help="최소 스팸 확률 (기본값: 0.35)",
    )
    parser.add_argument(
        "--max_score",
        type=float,
        default=0.65,
        help="최대 스팸 확률 (기본값: 0.65)",
    )
    parser.add_argument(
        "--max_train_samples",
        type=int,
        default=2000,
        help="최대 학습 샘플 수 (기본값: 2000)",
    )
    parser.add_argument(
        "--max_val_samples",
        type=int,
        default=200,
        help="최대 검증 샘플 수 (기본값: 200)",
    )

    args = parser.parse_args()

    # 파이프라인 실행
    pipeline = OptimizedTrainingPipeline(
        output_dir=args.output_dir,
        use_filtered_data=not args.no_filter,
        min_score=args.min_score,
        max_score=args.max_score,
        max_train_samples=args.max_train_samples,
        max_val_samples=args.max_val_samples,
    )

    pipeline.run()


if __name__ == "__main__":
    main()
