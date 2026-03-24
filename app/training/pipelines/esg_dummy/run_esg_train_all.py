"""
ESG 더미 한방 학습: 레이블 데이터 생성 → error_type 엑사원 SFT → usage 시계열 예측.

실행 (app 디렉터리에서):
  cd C:\\dev\\RAG\\app
  python -m training.pipelines.esg_dummy.run_esg_train_all

  labeled_slots.csv 가 이미 있으면 1단계 스킵:
  python -m training.pipelines.esg_dummy.run_esg_train_all --skip-generate
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# app 루트를 path에 추가
_app_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_app_root) not in sys.path:
    sys.path.insert(0, str(_app_root))

from core.paths import get_esg_dummy_dir  # type: ignore  # app 하위 실행 시 core = app/core


def _format_elapsed(sec: float) -> str:
    if sec < 60:
        return f"{sec:.1f}초"
    return f"{int(sec // 60)}분 {sec % 60:.1f}초"


def main() -> None:
    parser = argparse.ArgumentParser(description="ESG 더미 한방 학습 (생성 → 분류 → 예측)")
    parser.add_argument("--skip-generate", action="store_true", help="labeled_slots.csv 있으면 1단계(데이터 생성) 스킵")
    parser.add_argument("--resume", action="store_true", help="SFT 학습을 최신 체크포인트에서 이어받기")
    args = parser.parse_args()

    data_dir = get_esg_dummy_dir()
    labeled_path = data_dir / "labeled_slots.csv"
    total_start = time.perf_counter()
    step_times: list[float] = []

    # 1) 레이블 데이터 생성 (선택)
    if not args.skip_generate or not labeled_path.exists():
        print("=" * 60)
        print("[1/4] labeled_slots.csv 생성 (run_generate_measurements --output-labeled)")
        print("=" * 60)
        t0 = time.perf_counter()
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "training.pipelines.esg_dummy.run_generate_measurements",
                "--output-labeled",
            ],
            cwd=str(_app_root),
        )
        elapsed = time.perf_counter() - t0
        step_times.append(elapsed)
        if r.returncode != 0:
            print("[FAIL] 데이터 생성 실패")
            sys.exit(1)
        print(f"[1/4] 완료: 소요 {_format_elapsed(elapsed)}")
    else:
        print("[1/4] skip (labeled_slots.csv 이미 존재)")
        step_times.append(0.0)

    # 2) error_type 엑사원 SFT: labeled_slots → chat JSONL → ExaOne LoRA
    print()
    print("=" * 60)
    print("[2/4] labeled_slots → esg_error_chat.jsonl 변환")
    print("=" * 60)
    t0 = time.perf_counter()
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "training.pipelines.esg_dummy.run_esg_to_chat_format",
        ],
        cwd=str(_app_root),
    )
    elapsed = time.perf_counter() - t0
    step_times.append(elapsed)
    if r.returncode != 0:
        print("[FAIL] chat JSONL 변환 실패")
        sys.exit(1)
    print(f"[2/4] 완료: 소요 {_format_elapsed(elapsed)}")

    print()
    print("=" * 60)
    print("[3/4] error_type 엑사원 SFT 학습 (EXAONE LoRA)")
    print("=" * 60)
    t0 = time.perf_counter()
    sft_cmd = [
        sys.executable,
        "-m",
        "training.pipelines.esg_dummy.run_esg_sft_training",
    ]
    if args.resume:
        sft_cmd.append("--resume")
    r = subprocess.run(sft_cmd, cwd=str(_app_root))
    elapsed = time.perf_counter() - t0
    step_times.append(elapsed)
    if r.returncode != 0:
        print("[FAIL] 엑사원 SFT 학습 실패")
        sys.exit(1)
    print(f"[3/4] 완료: 소요 {_format_elapsed(elapsed)}")

    # 4) usage 시계열 예측
    print()
    print("=" * 60)
    print("[4/4] usage 시계열 예측 학습")
    print("=" * 60)
    t0 = time.perf_counter()
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "training.pipelines.esg_dummy.train_usage_forecaster",
        ],
        cwd=str(_app_root),
    )
    elapsed = time.perf_counter() - t0
    step_times.append(elapsed)
    if r.returncode != 0:
        print("[FAIL] 예측 학습 실패")
        sys.exit(1)
    print(f"[4/4] 완료: 소요 {_format_elapsed(elapsed)}")

    total_elapsed = time.perf_counter() - total_start
    print()
    print("=" * 60)
    print("[OK] ESG 더미 한방 학습 완료")
    if step_times:
        print(f"     단계별: [1] {_format_elapsed(step_times[0])}  [2] {_format_elapsed(step_times[1])}  [3] {_format_elapsed(step_times[2])}  [4] {_format_elapsed(step_times[3])}")
    print(f"     총 소요: {_format_elapsed(total_elapsed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
