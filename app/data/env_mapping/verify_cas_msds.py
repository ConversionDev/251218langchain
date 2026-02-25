# -*- coding: utf-8 -*-
"""
원본(환경 데이터 매핑 테이블.xlsx) 대비 보강(환경데이터_매핑_보강.xlsx)에서
CAS 번호·MSDS 기준명이 기존 데이터 기준으로 제대로 채워졌는지 검증합니다.

실행 (프로젝트 루트에서 app 포함):
  python app/data/env_mapping/verify_cas_msds.py
  python app/data/env_mapping/verify_cas_msds.py --original app/data/env_mapping/환경\ 데이터\ 매핑\ 테이블.xlsx --output app/data/env_mapping/환경데이터_매핑_보강.xlsx
"""

import argparse
import re
import sys
from pathlib import Path

# 프로젝트 루트 = app의 상위 (RAG)
_app_dir = Path(__file__).resolve().parent.parent.parent  # app
_project_root = _app_dir.parent  # RAG
for _d in (_project_root, _app_dir):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def _normalize_cas(v) -> str:
    if v is None or (isinstance(v, float) and (v != v or v == 0)):
        return ""
    return re.sub(r"\s+", "", str(v).strip())


def _str(val) -> str:
    if val is None or (isinstance(val, float) and (val != val or val == 0)):
        return ""
    return str(val).strip()


def main():
    import pandas as pd
    from core.paths import get_env_mapping_data_dir

    data_dir = get_env_mapping_data_dir()
    parser = argparse.ArgumentParser(description="원본 vs 보강 CAS·MSDS 기준명 검증")
    parser.add_argument("--original", type=Path, default=data_dir / "환경 데이터 매핑 테이블.xlsx", help="원본 Excel")
    parser.add_argument("--output", type=Path, default=data_dir / "환경데이터_매핑_보강.xlsx", help="보강 Excel")
    args = parser.parse_args()

    if not args.original.exists():
        print(f"원본 파일 없음: {args.original}")
        sys.exit(1)
    if not args.output.exists():
        print(f"보강 파일 없음: {args.output}")
        sys.exit(1)

    orig_df = pd.read_excel(args.original, sheet_name=0)
    orig_df = orig_df.rename(columns=lambda x: str(x).strip() if isinstance(x, str) else x)
    out_df = pd.read_excel(args.output, sheet_name=0)
    out_df = out_df.rename(columns=lambda x: str(x).strip() if isinstance(x, str) else x)

    cas_col_orig = None
    for c in orig_df.columns:
        cnorm = re.sub(r"\s+", "", str(c).lower())
        if "cas" in cnorm and ("번호" in cnorm or cnorm == "cas"):
            cas_col_orig = c
            break
    cas_col_out = None
    for c in out_df.columns:
        cnorm = re.sub(r"\s+", "", str(c).lower())
        if "cas" in cnorm and ("번호" in cnorm or cnorm == "cas"):
            cas_col_out = c
            break
    msds_col_orig = "MSDS 기준명" if "MSDS 기준명" in orig_df.columns else None
    msds_col_out = "MSDS 기준명" if "MSDS 기준명" in out_df.columns else None

    if not cas_col_out:
        print("보강 파일에 CAS 번호 열이 없습니다.")
        sys.exit(1)

    # 원본 유니크 CAS 및 CAS별 MSDS 기준명 (하나라도 있는 것) / 원본에서 CAS 없이 있는 내부 표기명 (환경 지표 등)
    orig_cas_set = set()
    orig_cas_to_msds = {}
    orig_empty_cas_aliases = set()  # 원본에서 CAS 없이 있는 '내부 표기명' (BOD, COD, PM 등)
    alias_col_orig = "내부 표기명" if "내부 표기명" in orig_df.columns else None
    for _, row in orig_df.iterrows():
        cas = _normalize_cas(row.get(cas_col_orig))
        alias = _str(row.get(alias_col_orig)) if alias_col_orig else ""
        if not cas:
            if alias:
                orig_empty_cas_aliases.add(alias.strip().lower())
            continue
        orig_cas_set.add(cas)
        msds = _str(row.get(msds_col_orig)) if msds_col_orig else ""
        if msds and (cas not in orig_cas_to_msds or not orig_cas_to_msds[cas]):
            orig_cas_to_msds[cas] = msds

    # 보강: CAS 비어 있는 행, MSDS 비어 있는 행
    out_empty_cas = []
    out_empty_msds = []
    out_cas_set = set()
    for i, row in out_df.iterrows():
        cas = _normalize_cas(row.get(cas_col_out))
        msds = _str(row.get(msds_col_out)) if msds_col_out else ""
        alias = _str(row.get("내부 표기명", ""))
        if not cas:
            out_empty_cas.append((i + 2, alias))  # 1-based + header
        else:
            out_cas_set.add(cas)
        if not msds:
            out_empty_msds.append((i + 2, cas, alias))

    print("=" * 60)
    print("CAS 번호 · MSDS 기준명 검증")
    print("=" * 60)
    print(f"원본: {args.original.name}  행 수={len(orig_df)}, 유니크 CAS={len(orig_cas_set)}")
    print(f"보강: {args.output.name}   행 수={len(out_df)}, 유니크 CAS={len(out_cas_set)}")
    print()

    # 1) 보강에서 CAS 번호가 비어 있는 행
    if out_empty_cas:
        print(f"[문제] 보강에서 CAS 번호가 비어 있는 행: {len(out_empty_cas)}개")
        for row_idx, alias in out_empty_cas[:20]:
            print(f"  행 {row_idx}: 내부 표기명={alias!r}")
        if len(out_empty_cas) > 20:
            print(f"  ... 외 {len(out_empty_cas) - 20}개")
        print()
    else:
        print("[OK] 보강 모든 행에 CAS 번호 있음")
        print()

    # 2) 보강에서 MSDS 기준명이 비어 있는 행 (원본에 해당 CAS의 MSDS가 있는데도 비어 있으면 문제)
    missing_msds_from_orig = []
    for row_idx, cas, alias in out_empty_msds:
        if cas and orig_cas_to_msds.get(cas):
            missing_msds_from_orig.append((row_idx, cas, alias, orig_cas_to_msds[cas]))
    if missing_msds_from_orig:
        print(f"[문제] 원본에 MSDS 기준명이 있는데 보강에서 비어 있는 행: {len(missing_msds_from_orig)}개")
        for row_idx, cas, alias, expected_msds in missing_msds_from_orig[:15]:
            print(f"  행 {row_idx}: CAS={cas}, 내부표기명={alias!r}  → 원본 MSDS={expected_msds!r}")
        if len(missing_msds_from_orig) > 15:
            print(f"  ... 외 {len(missing_msds_from_orig) - 15}개")
        print()
    else:
        print("[OK] 원본에 MSDS가 있는 CAS는 보강에서도 MSDS 기준명이 채워짐")
        print()

    # 3) 보강에서 MSDS가 비어 있는 행 전체 (참고)
    print(f"[참고] 보강에서 MSDS 기준명이 비어 있는 행 총 {len(out_empty_msds)}개")
    print()

    # 4) 원본에만 있고 보강에 없는 CAS
    only_in_orig = orig_cas_set - out_cas_set
    if only_in_orig:
        print(f"[참고] 원본에만 있고 보강에 없는 CAS: {len(only_in_orig)}개")
        for cas in sorted(only_in_orig)[:15]:
            msds = orig_cas_to_msds.get(cas, "")
            print(f"  {cas}  (원본 MSDS: {msds!r})")
        if len(only_in_orig) > 15:
            print(f"  ... 외 {len(only_in_orig) - 15}개")
    else:
        print("[OK] 원본의 모든 CAS가 보강에 존재함")
    print()

    # 5) EC 번호 (보강에 열이 있으면)
    ec_col_out = "EC 번호" if "EC 번호" in out_df.columns else None
    if ec_col_out:
        out_empty_ec_with_cas = sum(
            1 for _, row in out_df.iterrows()
            if _normalize_cas(row.get(cas_col_out)) and not _str(row.get(ec_col_out))
        )
        if out_empty_ec_with_cas:
            print(f"[참고] 보강에서 CAS는 있으나 EC 번호가 비어 있는 행: {out_empty_ec_with_cas}개")
        else:
            print("[OK] CAS 있는 행은 EC 번호 모두 채워짐 (또는 해당 없음)")
    print("=" * 60)


if __name__ == "__main__":
    main()
