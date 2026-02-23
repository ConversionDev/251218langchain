"""원본 환경 데이터 테이블 + 매핑 Excel(CAS당 1행, 12개 언어)을 CAS 기준으로 합쳐서 저장. 원본 행 수 유지."""

import argparse
import re
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


def _normalize_cas(v) -> str:
    if v is None or (isinstance(v, float) and (v != v or v == 0)):
        return ""
    return re.sub(r"\s+", "", str(v).strip())


def main():
    import pandas as pd
    parser = argparse.ArgumentParser(description="원본 + 매핑 Excel 통합 (CAS 기준)")
    parser.add_argument("--original", type=Path, required=True, help="환경 데이터 매핑 테이블.xlsx")
    parser.add_argument("--mapping", type=Path, required=True, help="mapping_YYYYMMDD_HHMM.xlsx")
    parser.add_argument("--output", type=Path, required=True, help="출력 Excel")
    args = parser.parse_args()
    orig_df = pd.read_excel(args.original, sheet_name=0)
    map_df = pd.read_excel(args.mapping, sheet_name=0)
    orig_df = orig_df.rename(columns=lambda c: str(c).strip() if isinstance(c, str) else c)
    map_df = map_df.rename(columns=lambda c: str(c).strip() if isinstance(c, str) else c)
    cas_col_orig = None
    for c in orig_df.columns:
        if re.sub(r"\s+", "", str(c).lower()).find("cas") >= 0 and ("번호" in str(c) or c == "cas"):
            cas_col_orig = c
            break
    if not cas_col_orig:
        raise SystemExit("원본에 CAS 열이 없습니다.")
    cas_col_map = None
    for c in map_df.columns:
        if re.sub(r"\s+", "", str(c).lower()).find("cas") >= 0 and ("번호" in str(c) or c == "cas"):
            cas_col_map = c
            break
    if not cas_col_map:
        raise SystemExit("매핑에 CAS 열이 없습니다.")
    map_by_cas = {}
    for _, row in map_df.iterrows():
        cas = _normalize_cas(row.get(cas_col_map))
        if cas:
            map_by_cas[cas] = row.to_dict()
    lang_cols = [c for c in map_df.columns if c != cas_col_map and ("물질명" in str(c) or "동의어" in str(c) or "유사명" in str(c) or "검증" in str(c))]
    for c in lang_cols:
        if c not in orig_df.columns:
            orig_df[c] = None
    for i, row in orig_df.iterrows():
        cas = _normalize_cas(row.get(cas_col_orig))
        if cas and cas in map_by_cas:
            m = map_by_cas[cas]
            for c in lang_cols:
                if c in m and pd.notna(m.get(c)):
                    orig_df.at[i, c] = m[c]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    orig_df.to_excel(args.output, index=False, engine="openpyxl")
    print(f"저장: {args.output} (행: {len(orig_df)})")


if __name__ == "__main__":
    main()
