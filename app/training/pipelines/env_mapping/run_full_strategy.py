"""
전략 한 번에 실행: 원본 CAS 추출 → run_mapping(73개+배터리 12개 언어) → vocabulary_builder(보강 Excel).
.env 자동 로드로 KECI_SERVICE_KEY 사용.

실행 (app 디렉터리에서):
  python -m training.pipelines.env_mapping.run_full_strategy
  # 또는 경로 지정:
  python -m training.pipelines.env_mapping.run_full_strategy --original "data/env_mapping/환경 데이터 매핑 테이블.xlsx" --output data/env_mapping/환경데이터_매핑_보강.xlsx

1단계: 원본에서 유니크 CAS → base_for_mapping.csv
2단계: run_mapping → mapping_full_YYYYMMDD_HHMM.xlsx (ExaOne 12개 언어, 30분~1시간 소요 가능)
3단계: vocabulary_builder (.env 로드, PubChem·KECI) → 보강 Excel 저장
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


def _format_duration(seconds: float) -> str:
    s = int(round(seconds))
    if s < 60:
        return f"0:{s:02d}"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}:{s:02d}"
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def main() -> None:
    from core.paths import get_env_mapping_data_dir, get_project_root
    try:
        from dotenv import load_dotenv
        load_dotenv(get_project_root() / ".env", override=False)
    except ImportError:
        pass
    parser = argparse.ArgumentParser(
        description="환경 데이터 매핑 전략 한 번에 실행 (원본 CAS 추출 → ExaOne 매핑 → 보강 Excel)"
    )
    data_dir_default = get_env_mapping_data_dir()
    parser.add_argument("--original", type=Path, default=None, help="원본 Excel (기본: data/env_mapping/환경 데이터 매핑 테이블.xlsx)")
    parser.add_argument("--output", type=Path, default=None, help="보강 Excel 저장 경로 (기본: data/env_mapping/환경데이터_매핑_보강.xlsx)")
    parser.add_argument("--battery-csv", type=Path, default=None, help="배터리 CSV (기본: data/env_mapping/battery_substances.csv)")
    parser.add_argument("--no-pubchem", action="store_true", help="PubChem 보강 생략")
    parser.add_argument("--no-keci", action="store_true", help="KECI 보강 생략")
    parser.add_argument("--no-echa", action="store_true", help="ECHA 보강 생략")
    parser.add_argument("--stage", type=int, default=3, choices=(1, 2, 3), help="run_mapping 언어 단계 (기본 3=12개 언어)")
    parser.add_argument("--delay", type=float, default=0.5, help="ExaOne 호출 간 대기(초)")
    parser.add_argument("--pubchem-delay", type=float, default=0.2, help="PubChem/KECI 요청 간 대기(초)")
    parser.add_argument("--keci-service-key", type=str, default=None, help="KECI API 키 (미지정 시 환경변수)")
    args = parser.parse_args()

    original = Path(args.original) if args.original else data_dir_default / "환경 데이터 매핑 테이블.xlsx"
    output = Path(args.output) if args.output else data_dir_default / "환경데이터_매핑_보강.xlsx"
    if not original.exists():
        raise SystemExit(f"원본 파일 없음: {original}")
    data_dir = original.parent
    base_csv = data_dir / "base_for_mapping.csv"
    mapping_out = data_dir / f"mapping_full_{time.strftime('%Y%m%d_%H%M')}.xlsx"
    battery_csv = args.battery_csv or get_env_mapping_data_dir() / "battery_substances.csv"

    cwd = app_dir
    python = sys.executable
    env = os.environ.copy()
    start_total = time.perf_counter()

    print("")
    print("=" * 60)
    print("전략 한 번에 실행 시작")
    print("  1단계: 원본 CAS 추출 (수 초)")
    print("  2단계: ExaOne 12개 언어 매핑 (예상 30분~1시간, 물질 수에 따라 변동)")
    print("  3단계: vocabulary_builder — PubChem·KECI·중복제거 (수 분)")
    print("=" * 60)
    print("")

    step_start = time.perf_counter()
    print("=" * 60)
    print("1/3 원본에서 유니크 CAS 추출 → base_for_mapping.csv")
    print("=" * 60)
    r1 = subprocess.run(
        [
            python, "-m", "training.pipelines.env_mapping.export_original_cas_for_mapping",
            "--original", str(original.resolve()),
            "--output", str(base_csv.resolve()),
        ],
        cwd=str(cwd),
        env=env,
    )
    if r1.returncode != 0:
        raise SystemExit(f"1단계 실패: exit {r1.returncode}")
    elapsed1 = time.perf_counter() - step_start
    print(f"[1/3 완료] 경과: {_format_duration(elapsed1)} | 누적: {_format_duration(time.perf_counter() - start_total)}")

    print("")
    step_start = time.perf_counter()
    print("=" * 60)
    print("2/3 run_mapping (73개+배터리, 12개 언어) — ExaOne 호출로 시간 소요")
    print("=" * 60)
    r2 = subprocess.run(
        [
            python, "-m", "training.pipelines.env_mapping.run_mapping",
            "--input", str(base_csv.resolve()),
            "--output", str(mapping_out.resolve()),
            "--stage", str(args.stage),
            "--delay", str(args.delay),
        ],
        cwd=str(cwd),
        env=env,
    )
    if r2.returncode != 0:
        raise SystemExit(f"2단계 실패: exit {r2.returncode}")
    elapsed2 = time.perf_counter() - step_start
    print(f"[2/3 완료] 경과: {_format_duration(elapsed2)} | 누적: {_format_duration(time.perf_counter() - start_total)}")

    print("")
    step_start = time.perf_counter()
    print("=" * 60)
    print("3/3 vocabulary_builder (보강 Excel 저장)")
    print("=" * 60)
    cmd = [
        python, "-m", "training.pipelines.env_mapping.vocabulary_builder",
        "--original", str(original.resolve()),
        "--mapping", str(mapping_out.resolve()),
        "--output", str(output.resolve()),
        "--battery-csv", str(battery_csv.resolve()),
        "--pubchem-delay", str(args.pubchem_delay),
    ]
    if args.no_pubchem:
        cmd.append("--no-pubchem")
    if args.no_keci:
        cmd.append("--no-keci")
    if args.no_echa:
        cmd.append("--no-echa")
    if args.keci_service_key:
        cmd.extend(["--keci-service-key", args.keci_service_key])
    r3 = subprocess.run(cmd, cwd=str(cwd), env=env)
    if r3.returncode != 0:
        raise SystemExit(f"3단계 실패: exit {r3.returncode}")
    elapsed3 = time.perf_counter() - step_start
    total_elapsed = time.perf_counter() - start_total
    print("")
    print("=" * 60)
    print("전략 실행 완료")
    print("  출력:", output)
    print("  [3/3 경과]:", _format_duration(elapsed3))
    print("  [총 소요 시간]:", _format_duration(total_elapsed))
    print("=" * 60)


if __name__ == "__main__":
    main()
