"""원본 환경 데이터 매핑 테이블.xlsx에서 유니크 CAS를 뽑아 run_mapping 입력용 CSV 생성."""

import argparse
import csv
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
    parser = argparse.ArgumentParser(description="원본 Excel → 유니크 CAS CSV (run_mapping 입력용)")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    df = pd.read_excel(args.original, sheet_name=0)
    df = df.rename(columns=lambda x: str(x).strip() if isinstance(x, str) else x)
    cas_col = None
    for c in df.columns:
        cnorm = re.sub(r"\s+", "", str(c).lower())
        if "cas" in cnorm and ("번호" in cnorm or cnorm == "cas"):
            cas_col = c
            break
    if not cas_col:
        raise SystemExit("원본에 CAS 열이 없습니다.")
    name_en_col = "영문명" if "영문명" in df.columns else df.columns[0]
    name_ko_col = "MSDS 기준명" if "MSDS 기준명" in df.columns else None
    seen = set()
    rows = []
    for _, r in df.iterrows():
        cas = _normalize_cas(r.get(cas_col))
        if not cas or cas in seen:
            continue
        seen.add(cas)
        name_en = str(r.get(name_en_col) or "").strip()
        name_ko = str(r.get(name_ko_col) or "").strip() if name_ko_col else ""
        if not name_en and "내부 표기명" in df.columns:
            name_en = str(r.get("내부 표기명", "") or "").strip()
        rows.append({"cas": cas, "name_en": name_en or cas, "name_ko": name_ko})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cas", "name_en", "name_ko"])
        w.writeheader()
        w.writerows(rows)
    print(f"총 {len(rows)}개 CAS → {args.output}")


if __name__ == "__main__":
    main()
