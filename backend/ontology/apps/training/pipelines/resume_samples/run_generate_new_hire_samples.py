"""
신입사원 가상 이력서·역량 샘플 생성 파이프라인 (기본 300건).

ExaOne를 사용해 5대 Success DNA(리더십/기술력/창의성/협업/적응력)를 각각 대표하는
신입 후보 프로필을 생성하고, employees 테이블 호환 JSONL로 저장합니다.
저장 위치: app/data/resume/samples/new_hire_samples_YYYYMMDD_HHMM.jsonl

이 스크립트는 샘플 생성 시 원본 ExaOne만 사용합니다 (역량 어댑터 미로드).
실행 방법 (app 디렉터리에서):
  python -m training.pipelines.resume_samples.run_generate_new_hire_samples

옵션 (파싱 실패 방지: batch 3 + max 4096 권장):
  --count 300   생성 개수 (기본 300)
  --batch 3     호출당 생성 수 (기본 3, max 4096으로 잘림 방지)
  --delay 0.2   호출 간 대기(초)
  --adapter     역량 어댑터 사용 (기본: 미사용)
"""

import argparse
import os
import sys
from pathlib import Path

# 샘플 생성은 원본 ExaOne 권장 → 기본으로 역량 어댑터 미로드 (--adapter 주면 사용)
if "EXAONE_USE_COMPETENCY_ADAPTER" not in os.environ:
    os.environ["EXAONE_USE_COMPETENCY_ADAPTER"] = "false"

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from api.services.resume_sample_generator import run_and_save  # type: ignore
from core.paths import get_resume_samples_dir  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="신입사원 가상 샘플 생성 (ExaOne)")
    parser.add_argument("--count", type=int, default=300, help="생성할 샘플 수 (기본 300)")
    parser.add_argument("--batch", type=int, default=3, help="LLM 1회 호출당 생성 수 (기본 3, 파싱 실패 방지)")
    parser.add_argument("--delay", type=float, default=0.2, help="호출 간 대기 초 (기본 0.2)")
    parser.add_argument("--out-dir", type=Path, default=None, help="출력 디렉터리 (기본: data/resume/samples)")
    parser.add_argument("--prefix", type=str, default="new_hire_samples", help="파일명 접두사")
    parser.add_argument("--adapter", action="store_true", help="역량 어댑터 사용 (기본: 미사용, 원본 권장)")
    args = parser.parse_args()

    if args.adapter:
        os.environ["EXAONE_USE_COMPETENCY_ADAPTER"] = "true"
        print("[INFO] 역량 어댑터 사용")
    else:
        os.environ["EXAONE_USE_COMPETENCY_ADAPTER"] = "false"
        print("[INFO] 원본 ExaOne만 사용 (역량 어댑터 미로드)")

    out_dir = args.out_dir or get_resume_samples_dir()
    print(f"[INFO] 신입 샘플 생성 시작: count={args.count}, batch={args.batch}, out_dir={out_dir}")
    path = run_and_save(
        output_dir=out_dir,
        total_count=args.count,
        batch_size=args.batch,
        delay_seconds=args.delay,
        filename_prefix=args.prefix,
    )
    print(f"[INFO] 저장 완료: {path}")


if __name__ == "__main__":
    main()
