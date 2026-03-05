# -*- coding: utf-8 -*-
"""
배터리만 뽑아서 환경 데이터 매핑 테이블 형식으로 정리.
EC는 공급망 리스트 보강.xlsx + zvg-cas-list-d.xlsx 만 사용(API 없음).
다국어는 mapping Excel 있으면 활용해 12개 언어 행 확장.

실행 (app 또는 프로젝트 루트):
  python -m training.pipelines.env_mapping.build_battery_only
  python -m training.pipelines.env_mapping.build_battery_only --mapping data/env_mapping/mapping_full_20260223_2309.xlsx --output data/env_mapping/환경데이터_매핑_보강_배터리.xlsx
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# app 루트
_app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

from training.pipelines.env_mapping.vocabulary_builder import (
    ORIGINAL_COLUMNS,
    _normalize_cas,
    deduplicate_rows,
    expand_mapping_to_rows,
    parse_mapping_to_lang_dict,
    sort_rows_by_cas_and_language,
)
from training.pipelines.env_mapping.ec_from_xlsx import build_ec_by_cas


def load_battery_list(csv_path: Path) -> tuple[set[str], list[dict]]:
    """battery_substances.csv → (battery_cas_set, [{cas, name_en, name_ko}])."""
    cas_set = set()
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if str(row.get("battery_related", "0")).strip() not in ("1", "1.0", "Y", "y", "yes"):
                continue
            cas = _normalize_cas(row.get("cas", ""))
            if not cas:
                continue
            cas_set.add(cas)
            rows.append({
                "cas": cas,
                "name_en": (row.get("name_en") or "").strip(),
                "name_ko": (row.get("name_ko") or "").strip(),
            })
    return cas_set, rows


def rows_from_battery_list_only(
    battery_rows: list[dict],
    ec_by_cas: dict[str, str],
) -> list[dict]:
    """매핑 없이 battery_substances 기준으로 행 생성 (영문/국문 각 1행)."""
    out = []
    for r in battery_rows:
        cas = r["cas"]
        en = (r["name_en"] or r["name_ko"] or cas or "").strip()
        ko = (r["name_ko"] or r["name_en"] or "").strip()
        ec = ec_by_cas.get(cas, "")
        meta = {
            "표준그룹": "BAT",
            "영문명": en,
            "MSDS 기준명": ko,
            "EC 번호": ec,
            "관련 ESG 지표": "배터리 원자재",
            "산업 분류": "배터리 제조",
            "필수/선택": "필수",
            "표준 단위": "",
        }
        out.append({
            "내부 표기명": en,
            "표준그룹": meta["표준그룹"],
            "CAS 번호": cas,
            "EC 번호": meta["EC 번호"],
            "영문명": meta["영문명"],
            "MSDS 기준명": meta["MSDS 기준명"],
            "관련 ESG 지표": meta["관련 ESG 지표"],
            "산업 분류": meta["산업 분류"],
            "필수/선택": meta["필수/선택"],
            "표준 단위": meta["표준 단위"],
            "비고": "영문",
        })
        if ko and ko != en:
            out.append({
                "내부 표기명": ko,
                "표준그룹": meta["표준그룹"],
                "CAS 번호": cas,
                "EC 번호": meta["EC 번호"],
                "영문명": meta["영문명"],
                "MSDS 기준명": meta["MSDS 기준명"],
                "관련 ESG 지표": meta["관련 ESG 지표"],
                "산업 분류": meta["산업 분류"],
                "필수/선택": meta["필수/선택"],
                "표준 단위": meta["표준 단위"],
                "비고": "국문",
            })
    return out


def run(
    data_dir: Path,
    output_path: Path,
    mapping_path: Path | None = None,
    battery_csv_path: Path | None = None,
) -> None:
    import pandas as pd

    battery_csv = battery_csv_path or data_dir / "battery_substances.csv"
    if not battery_csv.exists():
        raise FileNotFoundError(f"배터리 목록 없음: {battery_csv}")

    battery_cas_set, battery_rows = load_battery_list(battery_csv)
    if not battery_cas_set:
        raise ValueError("battery_related=1 인 행이 없습니다.")

    # EC: 공급망 리스트 보강.xlsx + zvg-cas-list-d.xlsx 만 사용
    ec_by_cas = build_ec_by_cas(data_dir)

    if mapping_path and mapping_path.exists():
        # 다국어 활용: mapping에서 배터리 CAS만 필터 후 확장
        mapping_lang, _ = parse_mapping_to_lang_dict(mapping_path)
        mapping_lang_battery = {cas: mapping_lang[cas] for cas in battery_cas_set if cas in mapping_lang}
        # EC는 우리가 채운 ec_by_cas 사용 (mapping EC 무시)
        empty_df = pd.DataFrame(columns=ORIGINAL_COLUMNS)
        expanded = expand_mapping_to_rows(
            mapping_lang_battery,
            empty_df,
            "CAS 번호",
            battery_cas_set,
            mapping_ec_by_cas=ec_by_cas,
        )
        # 매핑에 없는 배터리 CAS는 battery_substances 기준으로 추가
        mapped_cas = set(mapping_lang_battery)
        missing = [r for r in battery_rows if r["cas"] not in mapped_cas]
        if missing:
            extra = rows_from_battery_list_only(missing, ec_by_cas)
            expanded = expanded + extra
        combined = expanded
    else:
        combined = rows_from_battery_list_only(battery_rows, ec_by_cas)

    combined = deduplicate_rows(combined, cas_key="CAS 번호", alias_key="내부 표기명")
    combined = sort_rows_by_cas_and_language(combined, cas_key="CAS 번호", note_key="비고")

    out_df = pd.DataFrame(combined, columns=ORIGINAL_COLUMNS)
    out_df = out_df.fillna("")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"저장: {output_path} (행 수: {len(out_df)}, CAS 수: {out_df['CAS 번호'].nunique()})")


def _find_latest_mapping(data_dir: Path) -> Path | None:
    """mapping_full_*.xlsx 또는 mapping_*.xlsx 중 최신 1개 반환."""
    full = sorted(data_dir.glob("mapping_full_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if full:
        return full[0]
    return next(iter(sorted(data_dir.glob("mapping_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)), None)


def main():
    from core.paths import get_env_mapping_data_dir, get_project_root
    try:
        from dotenv import load_dotenv
        load_dotenv(get_project_root() / ".env", override=False)
    except ImportError:
        pass

    data_dir = get_env_mapping_data_dir()
    default_mapping = _find_latest_mapping(data_dir)
    parser = argparse.ArgumentParser(description="배터리만 환경 데이터 매핑 형식으로 정리 (EC=공급망+zvg xlsx, 다국어=mapping)")
    parser.add_argument("--data-dir", type=Path, default=data_dir, help="data/env_mapping 경로")
    parser.add_argument("--mapping", type=Path, default=default_mapping, help="다국어 매핑 Excel (기본: data_dir 내 최신 mapping_full_*.xlsx)")
    parser.add_argument("--output", type=Path, default=None, help="출력 Excel (기본: data_dir/환경데이터_매핑_보강_배터리.xlsx)")
    parser.add_argument("--battery-csv", type=Path, default=None, help="배터리 목록 CSV (기본: data_dir/battery_substances.csv)")
    args = parser.parse_args()

    output = args.output or args.data_dir / "환경데이터_매핑_보강_배터리.xlsx"
    run(
        data_dir=args.data_dir,
        output_path=output,
        mapping_path=args.mapping,
        battery_csv_path=args.battery_csv,
    )


if __name__ == "__main__":
    main()
