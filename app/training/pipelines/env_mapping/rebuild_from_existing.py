"""
기존 데이터만으로 보강 Excel을 재생성합니다.
원본 Excel + 기존 매핑 Excel(mapping_*.xlsx)을 합쳐 CAS·MSDS 기준명을 원본 기준으로 채우고,
EC 번호가 비어 있으면 PubChem API로 조회해 채웁니다. (동의어용 PubChem/KECI/ECHA 호출은 생략)

실행 (app 디렉터리에서):
  python -m training.pipelines.env_mapping.rebuild_from_existing

  # 경로 지정
  python -m training.pipelines.env_mapping.rebuild_from_existing --original data/env_mapping/환경\ 데이터\ 매핑\ 테이블.xlsx --mapping data/env_mapping/mapping_full_20260223_2309.xlsx --output data/env_mapping/환경데이터_매핑_보강.xlsx

  # 매핑 미지정 시 data/env_mapping/ 내 최신 mapping_full_*.xlsx 또는 mapping_*.xlsx 자동 사용
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path


def _format_duration(seconds: float) -> str:
    s = int(round(seconds))
    if s < 60:
        return f"{s}초"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}분 {s}초"
    h, m = divmod(m, 60)
    return f"{h}시간 {m}분 {s}초"

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


def _find_latest_mapping(data_dir: Path) -> Path | None:
    """data_dir에서 최신 매핑 파일 1개 반환. mapping_full_*.xlsx 우선, 없으면 mapping_*.xlsx."""
    full = sorted(data_dir.glob("mapping_full_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if full:
        return full[0]
    fallback = sorted(data_dir.glob("mapping_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return fallback[0] if fallback else None


def main() -> None:
    from core.paths import get_env_mapping_data_dir, get_project_root
    from training.pipelines.env_mapping.vocabulary_builder import run as build_vocabulary

    try:
        from dotenv import load_dotenv
        load_dotenv(get_project_root() / ".env", override=False)
    except ImportError:
        pass

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data_dir = get_env_mapping_data_dir()
    parser = argparse.ArgumentParser(
        description="기존 원본+매핑만으로 보강 Excel 재생성 (외부 API 없이 빠르게)"
    )
    parser.add_argument("--original", type=Path, default=None, help="원본 Excel (기본: data/env_mapping/환경 데이터 매핑 테이블.xlsx)")
    parser.add_argument("--mapping", type=Path, default=None, help="매핑 Excel (미지정 시 폴더 내 최신 mapping_*.xlsx 사용)")
    parser.add_argument("--output", type=Path, default=None, help="보강 Excel 저장 경로 (기본: 환경데이터_매핑_보강.xlsx)")
    parser.add_argument("--battery-csv", type=Path, default=None, help="배터리 CSV (기본: battery_substances.csv)")
    parser.add_argument("--no-ec-api", action="store_true", help="EC 번호 API 보강(PubChem) 생략")
    args = parser.parse_args()

    original = args.original or data_dir / "환경 데이터 매핑 테이블.xlsx"
    output = args.output or data_dir / "환경데이터_매핑_보강.xlsx"
    battery_csv = args.battery_csv or data_dir / "battery_substances.csv"

    mapping = args.mapping
    if not mapping:
        mapping = _find_latest_mapping(data_dir)
        if not mapping:
            print("data/env_mapping/에 mapping_*.xlsx 또는 mapping_full_*.xlsx가 없습니다. --mapping 경로를 지정하세요.")
            sys.exit(1)
        print(f"사용 매핑 파일(최신): {mapping.name}")

    if not original.exists():
        print(f"원본 파일 없음: {original}")
        sys.exit(1)
    if not mapping.exists():
        print(f"매핑 파일 없음: {mapping}")
        sys.exit(1)

    print("")
    print("=" * 60)
    print("기존 데이터만으로 보강 Excel 재생성 (EC 번호는 API로 채움, 동의어용 PubChem/KECI/ECHA는 미사용)")
    print("  원본:", original.name)
    print("  매핑:", mapping.name)
    print("  출력:", output.name)
    print("=" * 60)
    print("")

    start = time.perf_counter()
    build_vocabulary(
        original_path=Path(original),
        mapping_path=Path(mapping),
        output_path=Path(output),
        battery_csv_path=Path(battery_csv) if battery_csv else None,
        skip_pubchem=True,
        skip_keci=True,
        skip_echa=True,
        skip_ec_api=args.no_ec_api,
    )
    elapsed = time.perf_counter() - start
    done_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("")
    print("=" * 60)
    print("작업 완료")
    print(f"  소요 시간: {_format_duration(elapsed)}")
    print(f"  완료 시각: {done_at}")
    print("  검증: python app/data/env_mapping/verify_cas_msds.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
