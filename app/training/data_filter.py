"""
데이터 필터링 유틸리티

역할: 학습 시간 최소화를 위한 데이터 필터링
- LLaMA로 전체 데이터 점수 계산
- 애매한 케이스만 추출 (0.35~0.65 구간)
- 다양성 보장 샘플링
"""

import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# app/ 디렉토리를 Python 경로에 추가
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.llm.providers.llama import LLaMAGate  # type: ignore
from domain.v1.spam.services.utils import (  # type: ignore
    load_jsonl,
    save_jsonl,
    extract_email_metadata,
    get_api_root,
)


def filter_ambiguous_cases(
    train_data: List[Dict[str, Any]],
    llama_gate: LLaMAGate,
    min_score: float = 0.35,
    max_score: float = 0.65,
    max_samples: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """애매한 케이스만 필터링.

    Args:
        train_data: 학습 데이터 리스트
        llama_gate: LLaMA 분류기
        min_score: 최소 스팸 확률
        max_score: 최대 스팸 확률
        max_samples: 최대 샘플 수 (None이면 제한 없음)

    Returns:
        필터링된 데이터 리스트
    """
    import numpy as np

    print("=" * 60)
    print("[INFO] 데이터 필터링 시작")
    print("=" * 60)
    print(f"전체 데이터: {len(train_data)}개")
    print(f"필터링 범위: {min_score} ~ {max_score}")
    print()

    # LLaMA로 점수 계산 (배치 처리로 최적화)
    print("[Step 1] LLaMA로 점수 계산 중... (배치 처리 최적화)")
    all_scores = []  # 전체 점수 저장 (분포 분석용)
    ambiguous_cases = []
    scores = []

    # 이메일 메타데이터 미리 추출
    email_metadata_list = [extract_email_metadata(item) for item in train_data]

    # 배치 크기 최적화 (GPU 메모리에 따라 자동 조정)
    # LLaMA 3.2 3B + 4bit 양자화 기준으로 더 큰 배치 가능
    batch_size = 32  # 16 → 32 (2배 증가, 속도 2배 향상)
    total_batches = (len(email_metadata_list) + batch_size - 1) // batch_size

    print(f"[INFO] 배치 크기: {batch_size} (총 {total_batches}개 배치)")
    print()

    # 조기 종료 최적화: 충분한 샘플을 찾으면 중단
    early_stop_threshold = max_samples * 2 if max_samples else None  # 여유있게 2배까지 수집

    # 배치 단위로 처리
    for batch_idx in range(total_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(email_metadata_list))
        batch_metadata = email_metadata_list[batch_start:batch_end]
        batch_items = train_data[batch_start:batch_end]

        # 진행 상황 출력 (더 자주)
        if (batch_idx + 1) % 5 == 0 or batch_idx == total_batches - 1:
            progress_pct = (batch_end / len(train_data)) * 100
            print(f"  처리 중: {batch_end}/{len(train_data)} ({progress_pct:.1f}%) - 애매한 케이스: {len(ambiguous_cases)}개")

        # 배치 예측 (더 큰 배치 크기 사용)
        try:
            batch_results = llama_gate.classify_spam_batch(batch_metadata, batch_size=batch_size)
        except Exception as e:
            print(f"[WARNING] 배치 처리 실패, 작은 배치로 재시도: {e}")
            # 폴백: 더 작은 배치로 재시도
            try:
                batch_results = llama_gate.classify_spam_batch(batch_metadata, batch_size=16)
            except Exception as e2:
                print(f"[WARNING] 작은 배치도 실패, 개별 처리로 전환: {e2}")
                batch_results = []
                for metadata in batch_metadata:
                    result = llama_gate.classify_spam(metadata)
                    batch_results.append(result)

        # 결과 처리
        for item, result in zip(batch_items, batch_results):
            spam_prob = result["spam_prob"]
            all_scores.append(spam_prob)  # 전체 점수 저장

            # 애매한 구간인지 확인
            if min_score <= spam_prob <= max_score:
                ambiguous_cases.append((item, spam_prob))
                scores.append(spam_prob)

        # 조기 종료: 충분한 샘플을 찾았으면 중단
        if early_stop_threshold and len(ambiguous_cases) >= early_stop_threshold:
            print(f"[INFO] 충분한 샘플 수집 완료 ({len(ambiguous_cases)}개), 조기 종료")
            break

    # 점수 분포 분석
    print()
    print("[INFO] 점수 분포 분석:")
    all_scores_array = np.array(all_scores)
    print(f"  - 평균: {np.mean(all_scores_array):.3f}")
    print(f"  - 표준편차: {np.std(all_scores_array):.3f}")
    print(f"  - 최소: {np.min(all_scores_array):.3f}")
    print(f"  - 최대: {np.max(all_scores_array):.3f}")
    print(f"  - 중앙값: {np.median(all_scores_array):.3f}")

    # 구간별 분포
    very_low = np.sum(all_scores_array < 0.2)
    low = np.sum((all_scores_array >= 0.2) & (all_scores_array < 0.35))
    ambiguous = np.sum((all_scores_array >= 0.35) & (all_scores_array <= 0.65))
    high = np.sum((all_scores_array > 0.65) & (all_scores_array <= 0.8))
    very_high = np.sum(all_scores_array > 0.8)

    print()
    print("[INFO] 구간별 분포:")
    print(f"  - 매우 낮음 (0.0~0.2): {very_low}개 ({very_low/len(all_scores)*100:.1f}%)")
    print(f"  - 낮음 (0.2~0.35): {low}개 ({low/len(all_scores)*100:.1f}%)")
    print(f"  - 애매함 (0.35~0.65): {ambiguous}개 ({ambiguous/len(all_scores)*100:.1f}%)")
    print(f"  - 높음 (0.65~0.8): {high}개 ({high/len(all_scores)*100:.1f}%)")
    print(f"  - 매우 높음 (0.8~1.0): {very_high}개 ({very_high/len(all_scores)*100:.1f}%)")
    print()

    # 경고: 점수 분포가 비정상적일 경우
    if np.std(all_scores_array) < 0.1:
        print("[WARNING] 점수 표준편차가 매우 낮습니다 (< 0.1)")
        print("[WARNING] LLaMA가 모든 데이터를 비슷하게 예측하고 있습니다.")
        print("[WARNING] 필터링 효과가 제한적일 수 있습니다.")
        print()

    if ambiguous / len(all_scores) > 0.9:
        print("[WARNING] 애매한 케이스가 90% 이상입니다.")
        print("[WARNING] LLaMA 모델이 제대로 작동하지 않을 수 있습니다.")
        print("[WARNING] 필터링 범위를 조정하거나 LLaMA 모델을 확인하세요.")
        print()

    print(f"[OK] 애매한 케이스: {len(ambiguous_cases)}개 ({len(ambiguous_cases)/len(train_data)*100:.1f}%)")
    print()

    # 다양성 보장 샘플링
    if max_samples and len(ambiguous_cases) > max_samples:
        print(f"[Step 2] 다양성 보장 샘플링 중... (최대 {max_samples}개)")
        # 점수 분포를 고려한 샘플링
        sampled = sample_diverse(ambiguous_cases, max_samples)
        print(f"[OK] 샘플링 완료: {len(sampled)}개")
        print()
        return sampled
    else:
        return [item for item, _ in ambiguous_cases]


def sample_diverse(
    cases: List[Tuple[Dict[str, Any], float]], n: int
) -> List[Dict[str, Any]]:
    """다양성 보장 샘플링.

    점수 분포를 고려하여 다양한 케이스를 선택.

    Args:
        cases: (데이터, 점수) 튜플 리스트
        n: 선택할 샘플 수

    Returns:
        샘플링된 데이터 리스트
    """
    if len(cases) <= n:
        return [item for item, _ in cases]

    # 점수 구간별로 분류
    bins = {
        "low": [],  # 0.35 ~ 0.45
        "mid": [],  # 0.45 ~ 0.55
        "high": [],  # 0.55 ~ 0.65
    }

    for item, score in cases:
        if score < 0.45:
            bins["low"].append((item, score))
        elif score < 0.55:
            bins["mid"].append((item, score))
        else:
            bins["high"].append((item, score))

    # 각 구간에서 균등하게 샘플링
    samples_per_bin = n // 3
    remainder = n % 3

    sampled = []
    for i, (bin_name, bin_cases) in enumerate(bins.items()):
        if bin_cases:
            n_samples = samples_per_bin + (1 if i < remainder else 0)
            n_samples = min(n_samples, len(bin_cases))
            bin_samples = random.sample(bin_cases, n_samples)
            sampled.extend([item for item, _ in bin_samples])

    # 부족한 경우 랜덤으로 추가
    if len(sampled) < n:
        remaining = [item for item, _ in cases if item not in sampled]
        needed = n - len(sampled)
        if remaining:
            additional = random.sample(remaining, min(needed, len(remaining)))
            sampled.extend(additional)

    # 셔플
    random.shuffle(sampled)

    return sampled


def filter_training_data(
    train_path: Path,
    val_path: Path,
    output_dir: Path,
    llama_gate: LLaMAGate,
    min_score: float = 0.35,
    max_score: float = 0.65,
    max_train_samples: Optional[int] = 2000,
    max_val_samples: Optional[int] = 200,
    train_ratio: float = 0.9,
    adaptive_filtering: bool = True,
) -> Tuple[Path, Path]:
    """학습 데이터 필터링 및 저장.

    Args:
        train_path: 원본 train.jsonl 경로
        val_path: 원본 val.jsonl 경로
        output_dir: 출력 디렉토리
        llama_gate: LLaMA 분류기
        min_score: 최소 스팸 확률
        max_score: 최대 스팸 확률
        max_train_samples: 최대 학습 샘플 수
        max_val_samples: 최대 검증 샘플 수
        train_ratio: 학습/검증 비율
        adaptive_filtering: 적응형 필터링 활성화 여부

    Returns:
        (필터링된 train.jsonl 경로, 필터링된 val.jsonl 경로)
    """
    print("=" * 60)
    print("[INFO] 학습 데이터 필터링 시작")
    print("=" * 60)
    print()

    # 데이터 로드
    print("[Step 1] 데이터 로드 중...")
    train_data = load_jsonl(train_path)
    val_data = load_jsonl(val_path)
    print(f"[OK] Train: {len(train_data)}개, Val: {len(val_data)}개")
    print()

    # 적응형 필터링: 점수 분포에 따라 범위 조정 (배치 처리 최적화)
    if adaptive_filtering:
        print("[Step 1.5] 점수 분포 사전 분석 중... (배치 처리)")
        import numpy as np

        # 샘플 데이터로 점수 분포 확인 (배치 처리로 최적화)
        sample_size = min(100, len(train_data))
        sample_data = train_data[:sample_size]
        sample_metadata = [extract_email_metadata(item) for item in sample_data]
        
        # 배치로 점수 계산
        sample_scores = []
        try:
            batch_results = llama_gate.classify_spam_batch(sample_metadata, batch_size=32)
            sample_scores = [r["spam_prob"] for r in batch_results]
        except Exception as e:
            print(f"[WARNING] 배치 처리 실패, 개별 처리: {e}")
            # 폴백: 개별 처리
            for metadata in sample_metadata:
                result = llama_gate.classify_spam(metadata)
                sample_scores.append(result["spam_prob"])

        sample_scores_array = np.array(sample_scores)
        std_dev = np.std(sample_scores_array)
        mean_score = np.mean(sample_scores_array)

        print(f"  샘플 점수 분포: 평균={mean_score:.3f}, 표준편차={std_dev:.3f}")

        # 표준편차가 너무 낮으면 필터링 범위 조정
        if std_dev < 0.1:
            print("[WARNING] 점수 분포가 매우 좁습니다. 필터링 범위를 확대합니다.")
            # 더 넓은 범위로 조정
            adjusted_min = max(0.1, mean_score - 0.3)
            adjusted_max = min(0.9, mean_score + 0.3)
            print(f"  조정된 범위: {adjusted_min:.2f} ~ {adjusted_max:.2f}")
            min_score = adjusted_min
            max_score = adjusted_max
        elif std_dev < 0.15:
            print("[INFO] 점수 분포가 좁습니다. 필터링 범위를 약간 확대합니다.")
            adjusted_min = max(0.2, mean_score - 0.25)
            adjusted_max = min(0.8, mean_score + 0.25)
            print(f"  조정된 범위: {adjusted_min:.2f} ~ {adjusted_max:.2f}")
            min_score = adjusted_min
            max_score = adjusted_max
        print()

    # 필터링
    print("[Step 2] Train 데이터 필터링 중...")
    filtered_train = filter_ambiguous_cases(
        train_data,
        llama_gate,
        min_score=min_score,
        max_score=max_score,
        max_samples=max_train_samples,
    )

    print("[Step 3] Val 데이터 필터링 중...")
    filtered_val = filter_ambiguous_cases(
        val_data,
        llama_gate,
        min_score=min_score,
        max_score=max_score,
        max_samples=max_val_samples,
    )

    # 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    filtered_train_path = output_dir / "train_filtered.jsonl"
    filtered_val_path = output_dir / "val_filtered.jsonl"

    print("[Step 4] 필터링된 데이터 저장 중...")
    save_jsonl(filtered_train, filtered_train_path)
    save_jsonl(filtered_val, filtered_val_path)
    print(f"[OK] 저장 완료:")
    print(f"  - {filtered_train_path} ({len(filtered_train)}개)")
    print(f"  - {filtered_val_path} ({len(filtered_val)}개)")
    print()

    print("=" * 60)
    print("[OK] 데이터 필터링 완료!")
    print("=" * 60)
    print()

    return filtered_train_path, filtered_val_path


def main():
    """메인 실행 함수."""
    import argparse

    parser = argparse.ArgumentParser(description="학습 데이터 필터링")
    parser.add_argument(
        "--train_path",
        type=str,
        default=None,
        help="원본 train.jsonl 경로 (None이면 자동 탐지)",
    )
    parser.add_argument(
        "--val_path",
        type=str,
        default=None,
        help="원본 val.jsonl 경로 (None이면 자동 탐지)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="출력 디렉토리 (None이면 자동 생성)",
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
    parser.add_argument(
        "--no-adaptive",
        action="store_true",
        help="적응형 필터링 비활성화",
    )

    args = parser.parse_args()

    # 경로 자동 탐지
    train_path = args.train_path
    val_path = args.val_path
    output_dir = args.output_dir

    if train_path is None or val_path is None:
        api_root = get_api_root()
        data_dir = api_root / "data" / "sft_dataset" / "processed"

        if train_path is None:
            train_path = str(data_dir / "train.jsonl")
        if val_path is None:
            val_path = str(data_dir / "val.jsonl")

    if output_dir is None:
        api_root = get_api_root()
        output_dir = str(api_root / "data" / "sft_dataset" / "filtered")

    # LLaMA 분류기 로드
    print("[INFO] LLaMA 분류기 로딩 중...")
    classifier = LLaMAGate()
    classifier.load_model()
    print()

    # 필터링 실행
    filter_training_data(
        train_path=Path(train_path),
        val_path=Path(val_path),
        output_dir=Path(output_dir),
        llama_gate=classifier,
        min_score=args.min_score,
        max_score=args.max_score,
        max_train_samples=args.max_train_samples,
        max_val_samples=args.max_val_samples,
        adaptive_filtering=not args.no_adaptive,
    )


if __name__ == "__main__":
    main()

