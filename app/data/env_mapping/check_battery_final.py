# -*- coding: utf-8 -*-
"""배터리데이터_다국어_교정완료_최종.xlsx 중복 및 번역 품질 검사.
검사만 수행(파일 수정 없음). 중복 제거 후 재검토 시 반드시 중복제거 파일 경로를 넘기세요.
  python check_battery_final.py
  python check_battery_final.py app/data/env_mapping/배터리데이터_다국어_교정완료_최종_중복제거.xlsx
"""
import sys
from pathlib import Path

import pandas as pd

OUTPUT_FILE = Path(__file__).resolve().parent / "check_battery_final_result.txt"
DATA_DIR = Path(__file__).resolve().parent

def has_hangul(s):
    if not s or not isinstance(s, str):
        return False
    return any("\uac00" <= c <= "\ud7a3" for c in s)

def main():
    # 인자로 경로 주면 그 파일 검사 (중복제거본 재검토용)
    if len(sys.argv) >= 2:
        path = Path(sys.argv[1])
    else:
        path = Path(r"c:\Users\kku10\Downloads\배터리데이터_다국어_교정완료_최종.xlsx")
        if not path.exists():
            path = DATA_DIR / "배터리데이터_다국어_교정완료_최종.xlsx"
    if not path.exists():
        print("파일 없음:", path)
        sys.exit(1)

    out_lines = []
    def log(*a):
        line = " ".join(str(x) for x in a)
        out_lines.append(line)
        print(line)

    log("검사 대상 파일:", path)
    df = pd.read_excel(path, sheet_name=0)
    df = df.rename(columns=lambda c: str(c).strip() if isinstance(c, str) else c)
    cols = list(df.columns)
    log("=== 열 이름 ===")
    log(cols)
    log("\n=== 행 수:", len(df), "===")

    # 열 추정
    alias_col = None
    cas_col = None
    note_col = None
    for c in cols:
        if "내부" in str(c) and "표기" in str(c):
            alias_col = c
        if "CAS" in str(c) and "번호" in str(c):
            cas_col = c
        if "비고" in str(c):
            note_col = c
    if not alias_col:
        alias_col = cols[0]
    if not cas_col:
        for c in cols:
            if "CAS" in str(c):
                cas_col = c
                break
    if not note_col:
        note_col = "비고" if "비고" in cols else (cols[-1] if cols else None)
    if note_col is not None and note_col not in df.columns:
        note_col = None

    # 1) 완전 중복 행
    dup_full = df[df.duplicated(keep=False)]
    if len(dup_full) > 0:
        log("\n--- [1] 완전 중복 행 (동일 내용 반복) ---")
        log("건수:", len(dup_full))
        log(dup_full[[c for c in [alias_col, cas_col, note_col] if c in df.columns]].head(20).to_string())
    else:
        log("\n--- [1] 완전 중복 행: 없음 ---")

    # 2) (CAS, 내부 표기명) 조합 중복
    if cas_col and alias_col:
        key = df[cas_col].astype(str).str.strip() + "|" + df[alias_col].astype(str).str.strip().str.lower()
        dup_key = df[key.duplicated(keep=False)]
        if len(dup_key) > 0:
            log("\n--- [2] (CAS, 내부 표기명) 조합 중복 ---")
            log("건수:", len(dup_key))
            sel = [c for c in [alias_col, cas_col, note_col] if c is not None and c in df.columns]
            log(dup_key[sel].drop_duplicates().head(30).to_string())
        else:
            log("\n--- [2] (CAS, 내부 표기명) 조합 중복: 없음 ---")

    # 3) 번역 품질: 비고가 '영문'인데 내부 표기명에 한글이 많음
    if note_col and alias_col and note_col in df.columns:
        note_vals = df[note_col].astype(str).str.strip()
        alias_vals = df[alias_col].astype(str)
        wrong_lang = []
        for idx, (i, row) in enumerate(df.iterrows()):
            excel_row = idx + 2  # 1=헤더, 2부터 데이터
            note = note_vals.iloc[idx] if idx < len(note_vals) else ""
            alias = alias_vals.iloc[idx] if idx < len(alias_vals) else ""
            if pd.isna(alias) or str(alias).strip() == "":
                wrong_lang.append((excel_row, str(note), "(비어있음)", "내부 표기명 비어 있음"))
                continue
            alias = str(alias).strip()
            # 영문 행인데 한글만 또는 한글이 주된 경우
            if "영문" in note and has_hangul(alias) and not any(c.isascii() and c.isalpha() for c in alias):
                wrong_lang.append((excel_row, note, alias, "영문인데 한글만 있음"))
            # 국문 행인데 한글이 하나도 없음 (영문만)
            if "국문" in note and not has_hangul(alias):
                wrong_lang.append((excel_row, note, alias, "국문인데 한글 없음(영문만)"))
        if wrong_lang:
            log("\n--- [3] 번역/언어 불일치 의심 ---")
            log("건수:", len(wrong_lang))
            for row_num, note, alias, msg in wrong_lang[:40]:
                log(f"  행{row_num} 비고={note} | 내부표기명={str(alias)[:50]} | {msg}")
            if len(wrong_lang) > 40:
                log("  ... 외", len(wrong_lang) - 40, "건")
        else:
            log("\n--- [3] 번역/언어 불일치 의심: 없음 ---")

    # 4) 동일 CAS에 대해 동일 내부 표기명이 여러 언어로 반복 (실제로는 번역이 같음)
    if cas_col and alias_col and note_col and note_col in df.columns:
        by_cas = df.groupby(df[cas_col].astype(str).str.strip())
        same_text_diff_note = []
        for cas, grp in by_cas:
            aliases = grp[alias_col].astype(str).str.strip().str.lower()
            notes = grp[note_col].astype(str)
            if aliases.nunique() == 1 and notes.nunique() > 1:
                same_text_diff_note.append((cas, aliases.iloc[0], list(notes.unique())))
        if same_text_diff_note:
            log("\n--- [4] 동일 CAS에서 내부 표기명 동일한데 비고(언어)만 다름 (번역 누락 가능) ---")
            log("건수:", len(same_text_diff_note))
            for cas, alias, notes in same_text_diff_note[:25]:
                log(f"  CAS={cas} 내부표기명={str(alias)[:45]} 비고={notes}")
            if len(same_text_diff_note) > 25:
                log("  ... 외", len(same_text_diff_note) - 25, "건")
        else:
            log("\n--- [4] 동일 CAS 내 동일 표기명·다른 언어: 없음 ---")

    # 5) 빈 내부 표기명
    if alias_col:
        empty_alias = df[df[alias_col].isna() | (df[alias_col].astype(str).str.strip() == "")]
        if len(empty_alias) > 0:
            log("\n--- [5] 내부 표기명 비어 있는 행 ---")
            log("건수:", len(empty_alias))
        else:
            log("\n--- [5] 내부 표기명 비어 있는 행: 없음 ---")

    log("\n=== 검사 완료 ===")
    OUTPUT_FILE.write_text("\n".join(out_lines), encoding="utf-8")

if __name__ == "__main__":
    main()
