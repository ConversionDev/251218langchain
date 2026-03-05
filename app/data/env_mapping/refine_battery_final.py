# -*- coding: utf-8 -*-
"""
배터리데이터 다국어 정제: (1) 국문 방치 (2) 비정형 표기명 (3) 포르투갈어 중복/오타 (4) 비고 'XX 표준' 형식 통일.
+ (5) 96-49-1 국문 잔존 치환 (6) 일본어 오타 (7) carbonate/carbonato 유사 정규화·중복 제거 (8) 고분자 EC Exempted (9) 중국어 비정형→표준.
입력: 중복제거.xlsx 권장. 출력: _정제.xlsx
"""
from pathlib import Path

import pandas as pd

ALIAS_COL = "내부 표기명"
CAS_COL = "CAS 번호"
NOTE_COL = "비고"
EN_COL = "영문명"
EC_COL = "EC 번호"

# 비고에 이 문자열이 있으면 해당 언어 행 → 내부 표기명은 그 언어여야 함 (국문이면 오류)
LANG_LABELS = ("독일어", "프랑스어", "스페인어", "포르투갈어", "베트남어", "태국어", "인도네시아어", "아랍어", "중국어", "일본어")

# (5) 비고 언어에 맞는 표기명 치환: (CAS, 비고에 포함될 문자열) → 치환명
# 에틸렌 카보네이트(96-49-1) 하단부 국문 잔존: 비고가 외국어인데 내부 표기명이 "에틸렌 카보네이트"인 행 전체 보정
LANG_ALIAS_OVERRIDES = [
    ("96-49-1", "독일어", "Ethylencarbonat"),
    ("96-49-1", "프랑스어", "Carbonate d'éthylène"),
    ("96-49-1", "스페인어", "Carbonato de etileno"),
    ("96-49-1", "포르투갈어", "Carbonato de etileno"),
]

# (6) 일본어 화학 용어 오타·표준 표기 (순서대로 적용: 硫洪酸→硫酸, ニッケル(II)硫酸→硫酸ニッケル(II))
JA_ALIAS_FIXES = [
    ("硫洪酸", "硫酸"),
    ("ニッケル(II)硫酸", "硫酸ニッケル(II)"),  # 표준 어순: 황산니켈
]

# (9) 중국어 비정형/번역 오류 → 표준 기술 용어 (Ethylene carbonate, NMP 등)
ZH_ALIAS_FIXES = [
    ("气猴酸二酷酰", "碳酸乙烯酯"),   # 에틸렌 카보네이트 표준명
    # 추가 비정형 패턴 발견 시 여기에 (잘못된 표기, 표준명) 추가
]

# (8) 고분자 등 규제 Exempted CAS → EC 번호 'Exempted' 확정
POLYMER_CAS_EC_EXEMPTED = ("9003-04-7", "24937-79-9")  # SBR, PVDF

# 비고 정규화: 매핑 (비고에 포함된 문자열 → 통일된 "XX 표준" 형식)
NOTE_TO_STANDARD = [
    ("스페인어", "스페인어 표준"),
    ("포르투갈어", "포르투갈어 표준"),  # 스페인어/포르투갈어 동일 표기면 수동으로 "스페인어/포르투갈어 표준" 가능
    ("독일어", "독일어 표준"),
    ("프랑스어", "프랑스어 표준"),
    ("베트남어", "베트남어 표준"),
    ("태국어", "태국어 표준"),
    ("인도네시아어", "인도네시아어 표준"),
    ("아랍어", "아랍어 표준"),
    ("중국어", "중국어 표준"),
    ("일본어", "일본어 표준"),
    ("국문", "국문 표준"),
    ("영문", "영문 표준"),
]


def _has_hangul(s):
    if not s or not isinstance(s, str):
        return False
    return any("\uac00" <= c <= "\ud7a3" for c in str(s))


def _note_expects_non_korean(note):
    if not note or not isinstance(note, str):
        return False
    n = str(note).strip()
    return any(lang in n for lang in LANG_LABELS)


def _is_korean_only_or_dominant(alias):
    """내부 표기명이 한글만 또는 한글이 주된 경우."""
    if not alias or not isinstance(alias, str):
        return False
    s = str(alias).strip()
    if not s:
        return False
    if not _has_hangul(s):
        return False
    # 한글 + 숫자/괄호만 있거나, 라틴 문자가 거의 없으면 한글 주된 것으로 봄
    latin = sum(1 for c in s if c.isascii() and c.isalpha())
    return latin <= 2


def _is_messy_alias(alias):
    """비정형: | 포함, 또는 문장형(설명문) 의심."""
    if not alias or not isinstance(alias, str):
        return False
    s = str(alias).strip()
    if "|" in s:
        return True
    # 베트남어 설명문 패턴 (kết, tính sinh 등 + 긴 문장)
    low = s.lower()
    if any(x in low for x in ("kết", "tính sinh", " sinhh ")) or ("ethylene carbonate" in low and len(s) > 35):
        if len(s) > 40 or s.count(" ") >= 3:
            return True
    if len(s) > 50 and s.count(" ") >= 4:
        return True
    return False


def _normalize_note_to_standard(note):
    """비고를 '영문 표준', '국문 표준', '독일어 표준' 등으로 통일. 이미 '표준' 포함 시 유지, 세미콜론 뒤 보조 설명은 유지."""
    if not note or not isinstance(note, str):
        return note
    s = str(note).strip()
    if "표준" in s:
        return s
    for key, standard in NOTE_TO_STANDARD:
        if s == key or s.startswith(key + ";") or s.startswith(key + " "):
            # '국문; 무수물과...' → '국문 표준; 무수물과...'
            return standard + s[len(key):]
        if key in s and (s.startswith(key) or ";" + key in s or " " + key in s):
            return standard
    return s


def _normalize_pt_name(s):
    """포르투갈어 표기명 정규화 (오타 수정, 소문자)."""
    if not s or not isinstance(s, str):
        return ""
    t = str(s).strip().lower()
    t = t.replace("carbonoato", "carbonato")
    t = t.replace("carbonate de", "carbonato de")
    t = t.replace("carbonato de ácido etileno", "carbonato de etileno")
    t = " ".join(t.split())
    return t


def _normalize_ethyl_carbonate_alias(alias):
    """carbonate de etileno / carbonato de etileno → 동일 표준형으로 정규화 (유사 명칭 중복 제거용)."""
    if not alias or not isinstance(alias, str):
        return alias
    s = str(alias).strip()
    lower = s.lower()
    if "carbonate de etileno" in lower or "carbonato de etileno" in lower:
        return "Carbonato de etileno"
    return s


def run(input_path: Path, output_path: Path) -> None:
    df = pd.read_excel(input_path, sheet_name=0)
    df = df.rename(columns=lambda c: str(c).strip() if isinstance(c, str) else c)

    if ALIAS_COL not in df.columns or CAS_COL not in df.columns:
        raise ValueError("필요 열 없음: 내부 표기명, CAS 번호")

    note_col = NOTE_COL if NOTE_COL in df.columns else None
    en_col = EN_COL if EN_COL in df.columns else None

    # CAS별 영문명 캐시 (해당 CAS의 영문명이 있는 첫 행)
    cas_to_en = {}
    if en_col:
        for _, row in df.iterrows():
            cas = str(row.get(CAS_COL, "")).strip()
            en = row.get(en_col)
            if cas and en and pd.notna(en) and str(en).strip():
                if cas not in cas_to_en:
                    cas_to_en[cas] = str(en).strip()

    fixes_lang = 0
    fixes_messy = 0
    fixes_override = 0
    fixes_ja = 0
    fixes_zh = 0

    # (4) 비고를 "영문 표준", "국문 표준", "독일어 표준" 등 형식으로 통일
    if note_col:
        df[note_col] = df[note_col].astype(str).apply(lambda x: _normalize_note_to_standard(x) if pd.notna(x) and str(x).strip() else x)

    for i in df.index:
        alias = df.at[i, ALIAS_COL]
        if pd.isna(alias):
            continue
        alias_str = str(alias).strip()
        cas = str(df.at[i, CAS_COL]).strip()
        note = str(df.at[i, note_col]).strip() if note_col and pd.notna(df.at[i, note_col]) else ""

        # (5) 96-49-1 하단부 다국어 국문 잔존: 비고가 독일어/프랑스어/…(예: "독일어; 높은 유전율…")인데 내부 표기명이 "에틸렌 카보네이트" → 해당 언어 표준명으로 일괄 치환
        applied_override = False
        is_ethylene_korean = (
            alias_str == "에틸렌 카보네이트"
            or ("에틸렌 카보네이트" in alias_str and _has_hangul(alias_str))
        )
        for cas_key, lang_sub, replacement in LANG_ALIAS_OVERRIDES:
            if cas != cas_key or lang_sub not in note:
                continue
            en_for_cas = cas_to_en.get(cas_key, "")
            if is_ethylene_korean or _is_korean_only_or_dominant(alias_str) or (en_for_cas and alias_str == en_for_cas):
                df.at[i, ALIAS_COL] = replacement
                fixes_override += 1
                applied_override = True
                alias_str = replacement
                break
        if applied_override:
            continue

        # (9) 중국어 비정형 표기 → 표준 기술 용어 (碳酸乙烯酯, N-甲基吡咯烷酮 등)
        if note_col and "중국어" in note:
            for bad, standard in ZH_ALIAS_FIXES:
                if bad in alias_str:
                    df.at[i, ALIAS_COL] = alias_str.replace(bad, standard)
                    fixes_zh += 1
                    alias_str = str(df.at[i, ALIAS_COL]).strip()
                    break

        # (6) 일본어 오타·표준 표기: 硫洪酸→硫酸, ニッケル(II)硫酸→硫酸ニッケル(II) (순서대로 적용)
        for old_str, new_str in JA_ALIAS_FIXES:
            if old_str in alias_str:
                df.at[i, ALIAS_COL] = alias_str.replace(old_str, new_str)
                fixes_ja += 1
                alias_str = str(df.at[i, ALIAS_COL]).strip()

        # (1) 국문 방치: 비고는 독일어/프랑스어/… 인데 내부 표기명이 한글
        if note_col and _note_expects_non_korean(note) and _is_korean_only_or_dominant(alias_str):
            fallback = ""
            if en_col and pd.notna(df.at[i, en_col]):
                fallback = str(df.at[i, en_col]).strip()
            if not fallback and cas:
                fallback = cas_to_en.get(cas, "")
            if fallback:
                df.at[i, ALIAS_COL] = fallback
                fixes_lang += 1

        # (2) 비정형 표기명 → 영문명으로 대체
        elif _is_messy_alias(alias_str):
            fallback = ""
            if en_col and pd.notna(df.at[i, en_col]):
                fallback = str(df.at[i, en_col]).strip()
            if not fallback and cas:
                fallback = cas_to_en.get(cas, "")
            if fallback:
                df.at[i, ALIAS_COL] = fallback
                fixes_messy += 1

    # (3) 포르투갈어 중복: 비고에 '포르투갈어' 포함 행만, (CAS, 정규화된 표기명) 기준 1행만 유지
    if note_col and "포르투갈어" in df[note_col].astype(str).str.cat():
        df["_pt_norm"] = df[ALIAS_COL].astype(str).apply(_normalize_pt_name)
        df["_note_pt"] = df[note_col].astype(str).str.contains("포르투갈어", na=False)
        pt_mask = df["_note_pt"]
        pt_df = df[pt_mask].copy()
        pt_df["_cas"] = pt_df[CAS_COL].astype(str).str.strip()
        pt_key = pt_df["_cas"] + "|" + pt_df["_pt_norm"]
        pt_keep_idx = []
        for k, grp in pt_key.groupby(pt_key):
            # 같은 (CAS, 정규화명) 그룹에서 하나만 유지: 가장 짧은 원문 또는 첫 행
            idxs = grp.index.tolist()
            if len(idxs) <= 1:
                pt_keep_idx.extend(idxs)
                continue
            # 오타가 적은 것 우선: 'carbonoato' 없고, 길이 짧은 것
            best = idxs[0]
            best_len = len(str(df.at[best, ALIAS_COL]))
            for j in idxs[1:]:
                a = str(df.at[j, ALIAS_COL])
                if "carbonoato" not in a.lower() and len(a) < best_len:
                    best = j
                    best_len = len(a)
            pt_keep_idx.append(best)
        pt_drop = pt_df.index.difference(pd.Index(pt_keep_idx))
        df = df.drop(index=pt_drop)
        df = df.drop(columns=["_pt_norm", "_note_pt"], errors="ignore")
    else:
        df = df.drop(columns=["_pt_norm", "_note_pt"], errors="ignore")

    # (7) carbonate/carbonato 유사 명칭 정규화 후 (CAS, 표기명) 중복 제거
    n_before = len(df)
    df[ALIAS_COL] = df[ALIAS_COL].astype(str).apply(_normalize_ethyl_carbonate_alias)
    df = df.drop_duplicates(subset=[CAS_COL, ALIAS_COL], keep="first")
    df = df.reset_index(drop=True)
    fixes_ethyl_dedup = n_before - len(df)

    # (8) 고분자(SBR, PVDF 등) EC 번호 Exempted 확정
    if EC_COL in df.columns:
        mask = df[CAS_COL].astype(str).str.strip().isin(POLYMER_CAS_EC_EXEMPTED)
        if mask.any():
            df.loc[mask, EC_COL] = "Exempted"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"저장: {output_path}")
    print(f"(1) 국문 방치: {fixes_lang}건 (5) 96-49-1 언어별 치환: {fixes_override}건 (6) 일본어: {fixes_ja}건 (9) 중국어 정규화: {fixes_zh}건")
    print(f"(2) 비정형 표기명: {fixes_messy}건 (3)(7) 포르투갈어·carbonate 중복 제거: {fixes_ethyl_dedup}건 (4)(8) 비고·EC. 최종 행 수: {len(df)}")


def main():
    data_dir = Path(__file__).resolve().parent
    input_path = data_dir / "배터리데이터_다국어_교정완료_최종_중복제거.xlsx"
    if not input_path.exists():
        input_path = data_dir / "배터리데이터_다국어_교정완료_최종.xlsx"
    if not input_path.exists():
        print("입력 파일 없음. 먼저 dedupe_battery_final.py 로 중복제거.xlsx 를 만드세요.")
        return
    output_path = data_dir / "배터리데이터_다국어_교정완료_최종_정제.xlsx"
    run(input_path, output_path)


if __name__ == "__main__":
    main()
