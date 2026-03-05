# -*- coding: utf-8 -*-
"""
배터리데이터_다국어_교정완료_최종.xlsx 중복 제거 및 비고-표기명 일치 정리.
- (CAS, 내부 표기명) 조합 기준으로 1행만 유지.
- 같은 조합이 여러 행이면, '비고'와 실제 표기명 언어가 맞는 행을 우선 유지.
  (예: "Ethylene Glycol"이 영문·일본어 두 행이면 영문 행만 남김)
"""
from pathlib import Path

import pandas as pd

ALIAS_COL = "내부 표기명"
CAS_COL = "CAS 번호"
NOTE_COL = "비고"


def _detect_lang(text):
    """내부 표기명 문자가 어떤 언어인지 추정. '영문','국문','중국어','일본어' 등."""
    if not text or not isinstance(text, str):
        return "영문"
    s = str(text).strip()
    if not s:
        return "영문"
    for c in s:
        if "\uac00" <= c <= "\ud7a3":
            return "국문"
        if "\u4e00" <= c <= "\u9fff":
            return "중국어"
        if "\u3040" <= c <= "\u309f" or "\u30a0" <= c <= "\u30ff":
            return "일본어"
    return "영문"


def _note_matches_lang(note, lang):
    """비고 문자열에 해당 언어 라벨이 포함돼 있으면 True."""
    if not note or not isinstance(note, str):
        return False
    n = str(note).strip()
    if lang == "국문":
        return "국문" in n
    if lang == "영문":
        return "영문" in n
    if lang == "중국어":
        return "중국어" in n
    if lang == "일본어":
        return "일본어" in n
    return False


def run(input_path: Path, output_path: Path) -> None:
    df = pd.read_excel(input_path, sheet_name=0)
    df = df.rename(columns=lambda c: str(c).strip() if isinstance(c, str) else c)

    if ALIAS_COL not in df.columns or CAS_COL not in df.columns:
        raise ValueError("필요 열 없음: 내부 표기명, CAS 번호")

    note_col = NOTE_COL if NOTE_COL in df.columns else None
    df["_cas_norm"] = df[CAS_COL].astype(str).str.strip()
    df["_alias_norm"] = df[ALIAS_COL].astype(str).str.strip().str.lower()

    # (CAS, 내부 표기명) 별로 그룹
    key = df["_cas_norm"] + "|" + df["_alias_norm"]
    keep_idx = []

    for k, idx_list in key.groupby(key).groups.items():
        indices = idx_list.tolist()
        if len(indices) == 1:
            keep_idx.append(indices[0])
            continue
        # 중복: 비고와 표기명 언어가 맞는 행 우선
        alias_val = df.loc[indices[0], ALIAS_COL]
        if pd.isna(alias_val):
            alias_val = ""
        alias_str = str(alias_val).strip()
        detected = _detect_lang(alias_str)
        chosen = None
        for i in indices:
            if note_col is None:
                chosen = i
                break
            note_val = df.loc[i, note_col]
            note_str = str(note_val) if pd.notna(note_val) else ""
            if _note_matches_lang(note_str, detected):
                chosen = i
                break
        if chosen is None:
            chosen = indices[0]
        keep_idx.append(chosen)

    out = df.loc[sorted(keep_idx)].drop(columns=["_cas_norm", "_alias_norm"], errors="ignore")
    out = out.reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_excel(output_path, index=False, engine="openpyxl")
    print(f"저장: {output_path}")
    print(f"원본 행 수: {len(df)} → 중복 제거 후: {len(out)} (제거: {len(df) - len(out)})")


def main():
    input_path = Path(__file__).resolve().parent / "배터리데이터_다국어_교정완료_최종.xlsx"
    if not input_path.exists():
        input_path = Path(r"c:\Users\kku10\Downloads\배터리데이터_다국어_교정완료_최종.xlsx")
    if not input_path.exists():
        print("입력 파일 없음. app/data/env_mapping/배터리데이터_다국어_교정완료_최종.xlsx 또는 Downloads 폴더에 두세요.")
        return

    output_path = Path(__file__).resolve().parent / "배터리데이터_다국어_교정완료_최종_중복제거.xlsx"
    run(input_path, output_path)


if __name__ == "__main__":
    main()
