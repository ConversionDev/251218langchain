"""
전체 전략: 원본(1행=1별칭) 유지 + 12개 언어 확장 + EC 번호 API(PubChem) + PubChem + KECI + ECHA → 보카 사전 Excel.

원본/매핑에 EC 번호가 없으면 CAS 기준으로 PubChem API에서 EC 번호를 조회해 채움.

실행 (app 디렉터리에서):
  python -m training.pipelines.env_mapping.vocabulary_builder --original "data/env_mapping/환경 데이터 매핑 테이블.xlsx" --mapping data/env_mapping/mapping_YYYYMMDD_HHMM.xlsx --output data/env_mapping/환경데이터_매핑_보강.xlsx

옵션: --no-ec-api, --no-pubchem, --no-keci, --no-echa, --pubchem-delay, --keci-service-key
"""

import argparse
import re
import sys
import time
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from .config import LANG_CODE_TO_LABEL

ORIGINAL_COLUMNS = [
    "내부 표기명", "표준그룹", "CAS 번호", "EC 번호", "영문명", "MSDS 기준명",
    "관련 ESG 지표", "산업 분류", "필수/선택", "표준 단위", "비고",
]


def _format_duration(seconds: float) -> str:
    s = int(round(seconds))
    if s < 60:
        return f"0:{s:02d}"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}:{s:02d}"
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _format_eta(seconds: float) -> str:
    if seconds < 0 or seconds >= 1e6:
        return "?"
    s = int(round(seconds))
    if s < 60:
        return f"약 {s}초"
    m, s = divmod(s, 60)
    if m < 60:
        return f"약 {m}분"
    h, m = divmod(m, 60)
    return f"약 {h}시간 {m}분" if m else f"약 {h}시간"


def _normalize_cas(v) -> str:
    if v is None or (isinstance(v, float) and (v != v or v == 0)):
        return ""
    return re.sub(r"\s+", "", str(v).strip())


def _has_hangul(text) -> bool:
    """내부 표기명에 한글이 포함돼 있으면 True."""
    if not text:
        return False
    s = str(text)
    return any("\uAC00" <= c <= "\uD7A3" or "\u1100" <= c <= "\u11FF" for c in s)


# 정렬용: 언어 순서 (영문 → 국문 → 중국어 → … → 아랍어)
LANG_ORDER = [label for _, label in LANG_CODE_TO_LABEL.items()]


def _infer_language_from_text(text) -> str:
    """내부 표기명 문자가 속한 언어를 추정해 라벨 반환 (영문, 국문, 중국어, 일본어, 아랍어, 태국어 등)."""
    if not text:
        return "영문"
    s = str(text).strip()
    if not s:
        return "영문"
    for c in s:
        if "\uAC00" <= c <= "\uD7A3" or "\u1100" <= c <= "\u11FF":
            return "국문"
        if "\u3040" <= c <= "\u309F" or "\u30A0" <= c <= "\u30FF":
            return "일본어"
        if "\u4E00" <= c <= "\u9FFF":
            return "중국어"
        if "\u0600" <= c <= "\u06FF":
            return "아랍어"
        if "\u0E00" <= c <= "\u0E7F":
            return "태국어"
    return "영문"


def _find_cas_column(df):
    for c in df.columns:
        if not c:
            continue
        cnorm = re.sub(r"\s+", "", str(c).lower())
        if "cas" in cnorm and ("번호" in cnorm or cnorm == "cas"):
            return c
    return None


def load_original(path: Path):
    import pandas as pd
    df = pd.read_excel(path, sheet_name=0)
    df = df.rename(columns=lambda x: str(x).strip() if isinstance(x, str) else x)
    df = df[[c for c in df.columns if c and "Unnamed" not in str(c)]]
    cols = [c for c in ORIGINAL_COLUMNS if c in df.columns]
    extra = [c for c in df.columns if c not in ORIGINAL_COLUMNS]
    df = df[cols + extra] if extra else df[cols]
    return df


def _parse_synonyms_cell(val) -> list[str]:
    if val is None or (isinstance(val, float) and (val != val or val == 0)):
        return []
    parts = [p.strip() for p in re.split(r"[·\n,;]", str(val).strip()) if p.strip()]
    return parts


def parse_mapping_to_lang_dict(mapping_path: Path) -> tuple[dict, dict]:
    """매핑 Excel → ({cas: {lang_code: {name, synonyms}}}, {cas: EC 번호})."""
    import pandas as pd
    df = pd.read_excel(mapping_path, sheet_name=0)
    df = df.rename(columns=lambda x: str(x).strip() if isinstance(x, str) else x)
    cas_col = None
    ec_col = None
    for c in df.columns:
        cnorm = re.sub(r"\s+", "", str(c).lower())
        if "cas" in cnorm and ("번호" in cnorm or cnorm == "cas"):
            cas_col = c
        if "ec" in cnorm and "번호" in cnorm:
            ec_col = c
    if not cas_col:
        return {}, {}
    result = {}
    ec_by_cas = {}
    for _, row in df.iterrows():
        cas = _normalize_cas(row.get(cas_col))
        if not cas:
            continue
        if ec_col is not None:
            v = row.get(ec_col)
            if v is not None and not (isinstance(v, float) and (v != v or v == 0)):
                ec_by_cas[cas] = str(v).strip()
            elif cas not in ec_by_cas:
                ec_by_cas[cas] = ""
        if cas not in result:
            result[cas] = {}
        for lang_code, label in LANG_CODE_TO_LABEL.items():
            name_col = f"물질명({label})"
            if name_col not in df.columns:
                name_col = f"물질명({label})"
            syn_col = f"동의어({label})"
            if syn_col not in df.columns:
                syn_col = f"유사명({label})"
            name = (row.get(name_col) or "")
            if hasattr(name, "strip"):
                name = str(name).strip()
            else:
                name = str(name or "").strip()
            syn_val = row.get(syn_col) or ""
            synonyms = _parse_synonyms_cell(syn_val)
            result[cas][lang_code] = {"name": name, "synonyms": synonyms}
    return result, ec_by_cas


def get_metadata_from_original(original_df, cas: str, cas_col: str):
    """원본에서 해당 CAS의 메타데이터 반환. 같은 CAS가 여러 행이면 MSDS 기준명·영문명이 채워진 행을 우선 선택."""
    import pandas as pd
    candidates = []
    for _, row in original_df.iterrows():
        if _normalize_cas(row.get(cas_col)) != cas:
            continue
        meta = {
            "표준그룹": row.get("표준그룹", ""),
            "영문명": row.get("영문명", ""),
            "MSDS 기준명": row.get("MSDS 기준명", ""),
            "EC 번호": row.get("EC 번호", ""),
            "관련 ESG 지표": row.get("관련 ESG 지표", ""),
            "산업 분류": row.get("산업 분류", ""),
            "필수/선택": row.get("필수/선택", ""),
            "표준 단위": row.get("표준 단위", ""),
        }
        # 빈 문자열/NaN 정규화
        for k in meta:
            v = meta[k]
            if v is None or (isinstance(v, float) and (v != v or v == 0)):
                meta[k] = ""
            else:
                meta[k] = str(v).strip()
        candidates.append(meta)
    if not candidates:
        return {}
    # MSDS 기준명이 있는 행 우선, 없으면 영문명이 있는 행 우선
    def score(m):
        msds = (m.get("MSDS 기준명") or "").strip()
        en = (m.get("영문명") or "").strip()
        return (1 if msds else 0, 1 if en else 0)
    best = max(candidates, key=score)
    return best


def expand_mapping_to_rows(
    mapping_lang_by_cas: dict,
    original_df,
    cas_col: str,
    battery_cas_set: set,
    mapping_ec_by_cas: dict | None = None,
) -> list[dict]:
    mapping_ec_by_cas = mapping_ec_by_cas or {}
    rows = []
    for cas, lang_data in mapping_lang_by_cas.items():
        meta = get_metadata_from_original(original_df, cas, cas_col)
        if not meta:
            meta = {
                "표준그룹": "BAT", "영문명": "", "MSDS 기준명": "", "EC 번호": "",
                "관련 ESG 지표": "배터리 원자재", "산업 분류": "배터리 제조",
                "필수/선택": "필수", "표준 단위": "",
            }
            en_data = lang_data.get("en", {})
            meta["영문명"] = (en_data.get("name") or "").strip()
            ko_data = lang_data.get("ko", {})
            meta["MSDS 기준명"] = (ko_data.get("name") or "").strip() or meta["영문명"]
            meta["EC 번호"] = mapping_ec_by_cas.get(cas, "")
        ec_val = (meta.get("EC 번호") or "").strip() or mapping_ec_by_cas.get(cas, "")
        for lang_code, label in LANG_CODE_TO_LABEL.items():
            data = lang_data.get(lang_code, {})
            name = (data.get("name") or "").strip()
            synonyms = data.get("synonyms") or []
            note = label  # 언어만 표시 (영문, 국문, 중국어, ...)
            if name:
                rows.append({
                    "내부 표기명": name, "표준그룹": meta.get("표준그룹", ""), "CAS 번호": cas,
                    "EC 번호": ec_val,
                    "영문명": meta.get("영문명", ""), "MSDS 기준명": meta.get("MSDS 기준명", ""),
                    "관련 ESG 지표": meta.get("관련 ESG 지표", ""), "산업 분류": meta.get("산업 분류", ""),
                    "필수/선택": meta.get("필수/선택", ""), "표준 단위": meta.get("표준 단위", ""), "비고": note,
                })
            for s in synonyms:
                if not s or not s.strip():
                    continue
                rows.append({
                    "내부 표기명": s.strip(), "표준그룹": meta.get("표준그룹", ""), "CAS 번호": cas,
                    "EC 번호": ec_val,
                    "영문명": meta.get("영문명", ""), "MSDS 기준명": meta.get("MSDS 기준명", ""),
                    "관련 ESG 지표": meta.get("관련 ESG 지표", ""), "산업 분류": meta.get("산업 분류", ""),
                    "필수/선택": meta.get("필수/선택", ""), "표준 단위": meta.get("표준 단위", ""), "비고": note,
                })
    return rows


def add_pubchem_rows(current_rows: list[dict], cas_col_key: str = "CAS 번호", delay_seconds: float = 0.2) -> list[dict]:
    from .pubchem_client import get_synonyms_for_cas, get_synonyms_for_cas_via_cid
    log = __import__("logging").getLogger(__name__)
    cas_to_existing = {}
    for r in current_rows:
        cas = _normalize_cas(r.get(cas_col_key))
        if not cas:
            continue
        alias = (r.get("내부 표기명") or "").strip()
        if cas not in cas_to_existing:
            cas_to_existing[cas] = set()
        cas_to_existing[cas].add(alias.lower())
    new_rows = []
    unique_cas = sorted(cas_to_existing.keys())
    total_cas = len(unique_cas)
    start_wall = time.perf_counter()
    for i, cas in enumerate(unique_cas):
        syns = get_synonyms_for_cas(cas, delay_seconds=delay_seconds)
        if not syns:
            syns = get_synonyms_for_cas_via_cid(cas, delay_seconds=delay_seconds)
        existing = cas_to_existing.get(cas, set())
        sample = next((r for r in current_rows if _normalize_cas(r.get(cas_col_key)) == cas), None)
        if not sample:
            continue
        for s in syns:
            if not s or s.lower() in existing:
                continue
            existing.add(s.lower())
            row = {k: sample.get(k, "") for k in ORIGINAL_COLUMNS}
            row["내부 표기명"] = s
            row["비고"] = _infer_language_from_text(s)
            new_rows.append(row)
        completed = i + 1
        elapsed = time.perf_counter() - start_wall
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = total_cas - completed
        eta_sec = remaining / rate if rate > 0 else 0
        pct = (completed / total_cas * 100) if total_cas else 0
        log.info("[%5.1f%%] PubChem %d/%d CAS | 경과 %s | 남은 %s", pct, completed, total_cas, _format_duration(elapsed), _format_eta(eta_sec))
    return current_rows + new_rows


def add_keci_rows(current_rows: list[dict], cas_col_key: str = "CAS 번호", service_key: str | None = None, delay_seconds: float = 0.2) -> list[dict]:
    from .keci_client import get_names_for_cas, get_service_key
    key = service_key or get_service_key()
    if not key:
        __import__("logging").getLogger(__name__).warning("KECI: ServiceKey 없음. 스킵.")
        return current_rows
    cas_to_existing = {}
    for r in current_rows:
        cas = _normalize_cas(r.get(cas_col_key))
        if not cas:
            continue
        alias = (r.get("내부 표기명") or "").strip()
        if cas not in cas_to_existing:
            cas_to_existing[cas] = set()
        cas_to_existing[cas].add(alias.lower())
    new_rows = []
    unique_cas = sorted(cas_to_existing.keys())
    total_cas = len(unique_cas)
    log = __import__("logging").getLogger(__name__)
    start_wall = time.perf_counter()
    for i, cas in enumerate(unique_cas):
        names = get_names_for_cas(cas, service_key=key, delay_seconds=delay_seconds)
        existing = cas_to_existing.get(cas, set())
        sample = next((r for r in current_rows if _normalize_cas(r.get(cas_col_key)) == cas), None)
        if not sample:
            continue
        for name in (names.get("name_en", ""), names.get("name_ko", "")):
            n = (name or "").strip()
            if not n or n.lower() in existing:
                continue
            existing.add(n.lower())
            row = {k: sample.get(k, "") for k in ORIGINAL_COLUMNS}
            row["내부 표기명"] = n
            row["비고"] = _infer_language_from_text(n)
            new_rows.append(row)
        completed = i + 1
        elapsed = time.perf_counter() - start_wall
        rate = completed / elapsed if elapsed > 0 else 0
        eta_sec = (total_cas - completed) / rate if rate > 0 else 0
        log.info("[%5.1f%%] KECI %d/%d CAS | 경과 %s", (completed / total_cas * 100) if total_cas else 0, completed, total_cas, _format_duration(elapsed))
    return current_rows + new_rows


def add_echa_rows(current_rows: list[dict], cas_col_key: str = "CAS 번호", delay_seconds: float = 0.2) -> list[dict]:
    import os
    from .echa_client import get_synonyms_for_cas
    if not (os.environ.get("ECHA_API_URL") or "").strip():
        __import__("logging").getLogger(__name__).info("ECHA: ECHA_API_URL 미설정. 스킵.")
        return current_rows
    cas_to_existing = {}
    for r in current_rows:
        cas = _normalize_cas(r.get(cas_col_key))
        if not cas:
            continue
        alias = (r.get("내부 표기명") or "").strip()
        if cas not in cas_to_existing:
            cas_to_existing[cas] = set()
        cas_to_existing[cas].add(alias.lower())
    new_rows = []
    unique_cas = sorted(cas_to_existing.keys())
    log = __import__("logging").getLogger(__name__)
    for i, cas in enumerate(unique_cas):
        syns = get_synonyms_for_cas(cas, delay_seconds=delay_seconds)
        existing = cas_to_existing.get(cas, set())
        sample = next((r for r in current_rows if _normalize_cas(r.get(cas_col_key)) == cas), None)
        if not sample:
            continue
        for s in syns:
            x = (s and str(s)).strip()
            if not x or x.lower() in existing:
                continue
            existing.add(x.lower())
            row = {k: sample.get(k, "") for k in ORIGINAL_COLUMNS}
            row["내부 표기명"] = x
            row["비고"] = _infer_language_from_text(x)
            new_rows.append(row)
    return current_rows + new_rows


def fill_ec_from_api(
    rows: list[dict],
    cas_key: str = "CAS 번호",
    ec_key: str = "EC 번호",
    delay_seconds: float = 0.2,
) -> None:
    """EC 번호가 비어 있는 CAS에 대해 PubChem API로 조회해 채움. rows를 in-place 수정."""
    from datetime import datetime, timedelta
    from .pubchem_client import get_ec_number_for_cas
    log = __import__("logging").getLogger(__name__)
    cas_without_ec = set()
    for r in rows:
        cas = _normalize_cas(r.get(cas_key))
        ec = (r.get(ec_key) or "").strip()
        if cas and not ec:
            cas_without_ec.add(cas)
    if not cas_without_ec:
        return
    unique_cas = sorted(cas_without_ec)
    total = len(unique_cas)
    log.info("EC 번호 API 보강: %d개 CAS (PubChem)", total)
    start_wall = time.perf_counter()
    for i, cas in enumerate(unique_cas):
        ec_val = get_ec_number_for_cas(cas, delay_seconds=delay_seconds)
        if ec_val:
            for r in rows:
                if _normalize_cas(r.get(cas_key)) == cas:
                    r[ec_key] = ec_val
        completed = i + 1
        elapsed = time.perf_counter() - start_wall
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = total - completed
        eta_sec = remaining / rate if rate > 0 else 0
        eta_time = (datetime.now() + timedelta(seconds=eta_sec)).strftime("%Y-%m-%d %H:%M:%S")
        log.info(
            "EC API %d/%d CAS | 속도: %.2f CAS/초 | 예상 완료 시각: %s",
            completed, total, rate, eta_time,
        )


def deduplicate_rows(rows: list[dict], cas_key: str = "CAS 번호", alias_key: str = "내부 표기명") -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        cas = _normalize_cas(r.get(cas_key))
        alias = (r.get(alias_key) or "").strip()
        key = (cas, alias.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _get_row_language(row: dict, note_key: str = "비고", alias_key: str = "내부 표기명") -> str:
    """행의 비고가 언어 라벨이면 그대로, 아니면 내부 표기명으로 언어 추정."""
    note = (row.get(note_key) or "").strip()
    if note in LANG_ORDER:
        return note
    return _infer_language_from_text(row.get(alias_key))


def _lang_sort_key(lang: str) -> int:
    """언어 라벨의 정렬 순서. 작을수록 먼저."""
    for i, L in enumerate(LANG_ORDER):
        if L == lang:
            return i
    return len(LANG_ORDER)


def sort_rows_by_cas_and_language(rows: list[dict], cas_key: str = "CAS 번호", note_key: str = "비고", alias_key: str = "내부 표기명") -> list[dict]:
    """CAS별 → 언어 순(영문→국문→중국어→…→아랍어) → 같은 언어 내에서는 내부 표기명 알파벳 순."""
    return sorted(
        rows,
        key=lambda r: (
            _normalize_cas(r.get(cas_key)),
            _lang_sort_key(_get_row_language(r, note_key, alias_key)),
            (r.get(alias_key) or "").strip().lower(),
        ),
    )


def run(original_path: Path, mapping_path: Path, output_path: Path, battery_csv_path: Path,
        skip_pubchem: bool = False, skip_keci: bool = False, skip_echa: bool = False,
        skip_ec_api: bool = False,
        pubchem_delay: float = 0.2, keci_service_key: str | None = None):
    import logging
    import pandas as pd
    log = logging.getLogger(__name__)
    start_run = time.perf_counter()
    log.info("원본 로드: %s", original_path)
    original_df = load_original(original_path)
    cas_col = _find_cas_column(original_df)
    if not cas_col:
        raise ValueError("원본에 CAS 열이 없습니다.")
    base_rows = original_df.to_dict("records")
    for r in base_rows:
        for k in list(r.keys()):
            v = r[k]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                r[k] = ""
        for col in ORIGINAL_COLUMNS:
            if col not in r:
                r[col] = ""
        if not str(r.get("비고") or "").strip() or str(r.get("비고")).strip() in ("", "nan"):
            r["비고"] = "국문" if _has_hangul(r.get("내부 표기명")) else "영문"
    battery_cas_set = set()
    if battery_csv_path and battery_csv_path.exists():
        import csv
        with open(battery_csv_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                c = _normalize_cas(row.get("cas", ""))
                if c:
                    battery_cas_set.add(c)
    log.info("매핑 파싱 및 12개 언어 행 확장: %s", mapping_path)
    mapping_lang, mapping_ec = parse_mapping_to_lang_dict(mapping_path)
    expanded = expand_mapping_to_rows(
        mapping_lang, original_df, cas_col, battery_cas_set, mapping_ec_by_cas=mapping_ec
    )
    combined = base_rows + expanded
    if not skip_ec_api:
        log.info("========== EC 번호 API 보강 (PubChem) ==========")
        fill_ec_from_api(combined, cas_key="CAS 번호", ec_key="EC 번호", delay_seconds=pubchem_delay)
    if not skip_pubchem:
        log.info("========== PubChem 보강 ==========")
        combined = add_pubchem_rows(combined, cas_col_key="CAS 번호", delay_seconds=pubchem_delay)
    if not skip_keci:
        log.info("========== KECI 보강 ==========")
        combined = add_keci_rows(combined, cas_col_key="CAS 번호", service_key=keci_service_key, delay_seconds=pubchem_delay)
    if not skip_echa:
        log.info("========== ECHA 보강 ==========")
        combined = add_echa_rows(combined, cas_col_key="CAS 번호", delay_seconds=pubchem_delay)
    log.info("중복 제거")
    combined = deduplicate_rows(combined)
    log.info("CAS별·언어 순서 정렬 (기존 → 영문→국문→중국어→…→아랍어 → PubChem → KECI → ECHA)")
    combined = sort_rows_by_cas_and_language(combined, cas_key="CAS 번호", note_key="비고")
    if not combined:
        raise ValueError("합쳐진 행이 없습니다.")
    out_df = pd.DataFrame(combined)
    cols = [c for c in ORIGINAL_COLUMNS if c in out_df.columns]
    out_df = out_df[cols]
    out_df = out_df.fillna("")  # CAS·EC·MSDS 등 빈 값 통일
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_excel(output_path, index=False, engine="openpyxl")
    log.info("저장: %s | 행: %d | 소요: %s", output_path, len(out_df), _format_duration(time.perf_counter() - start_run))


def main():
    import logging
    from core.paths import get_env_mapping_data_dir, get_project_root
    try:
        from dotenv import load_dotenv
        load_dotenv(get_project_root() / ".env", override=False)
    except ImportError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="환경 데이터 매핑 보강: 원본 + 12개 언어 + PubChem + KECI + ECHA")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--battery-csv", type=Path, default=None)
    parser.add_argument("--no-pubchem", action="store_true")
    parser.add_argument("--no-keci", action="store_true")
    parser.add_argument("--no-echa", action="store_true")
    parser.add_argument("--no-ec-api", action="store_true", help="EC 번호 API 보강(PubChem) 생략")
    parser.add_argument("--pubchem-delay", type=float, default=0.2)
    parser.add_argument("--keci-service-key", type=str, default=None)
    args = parser.parse_args()
    battery_csv = args.battery_csv or (get_env_mapping_data_dir() / "battery_substances.csv")
    run(
        original_path=args.original,
        mapping_path=args.mapping,
        output_path=args.output,
        battery_csv_path=battery_csv,
        skip_pubchem=args.no_pubchem,
        skip_keci=args.no_keci,
        skip_echa=args.no_echa,
        skip_ec_api=args.no_ec_api,
        pubchem_delay=args.pubchem_delay,
        keci_service_key=args.keci_service_key,
    )


if __name__ == "__main__":
    main()
