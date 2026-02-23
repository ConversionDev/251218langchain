"""
환경 데이터 매핑 파이프라인: 다국어·배터리 물질 매핑 → Excel.

실행 (app 디렉터리에서):
  python -m training.pipelines.env_mapping.run_mapping

옵션:
  --input    베이스 물질 CSV/Excel 경로 (없으면 battery_substances.csv만 사용)
  --output   출력 Excel 경로 (기본: data/env_mapping/mapping_YYYYMMDD_HHMM.xlsx)
  --stage    1|2|3 (기본 3, 전체 12개 언어)
  --delay    ExaOne 호출 간 대기(초)
"""

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

if "EXAONE_USE_COMPETENCY_ADAPTER" not in os.environ:
    os.environ["EXAONE_USE_COMPETENCY_ADAPTER"] = "false"

from core.paths import get_env_mapping_data_dir  # type: ignore
from .config import ALL_LANGUAGES, STAGE_1_LANGUAGES, STAGE_2_LANGUAGES, STAGE_3_LANGUAGES
from .exaone_mapper import get_names_for_language
from .excel_writer import build_rows, write_excel
from .validator import validate_substance

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = get_env_mapping_data_dir()
BATTERY_CSV = DATA_DIR / "battery_substances.csv"


def load_substances_from_csv(path: Path) -> list[dict]:
    """CSV: cas, name_en, name_ko(선택), battery_related(0/1)."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cas = (r.get("cas") or "").strip()
            if not cas:
                continue
            name_en = (r.get("name_en") or "").strip()
            name_ko = (r.get("name_ko") or "").strip()
            battery = (r.get("battery_related") or "0").strip() in ("1", "Y", "y", "yes")
            rows.append({"cas": cas, "name_en": name_en, "name_ko": name_ko, "battery_related": battery})
    return rows


def load_base_substances(input_path: Path | None) -> list[dict]:
    """베이스 물질. 없으면 배터리 CSV만."""
    if input_path and input_path.exists():
        suffix = input_path.suffix.lower()
        if suffix == ".csv":
            return load_substances_from_csv(input_path)
        if suffix in (".xlsx", ".xls"):
            try:
                import pandas as pd
                df = pd.read_excel(input_path)
                df = df.rename(columns=lambda c: str(c).strip().lower().replace(" ", "_"))
                if "cas" not in df.columns or "name_en" not in df.columns:
                    raise ValueError("Excel에 cas, name_en 필요")
                rows = []
                for _, r in df.iterrows():
                    cas = str(r.get("cas", "")).strip()
                    if not cas or cas == "nan":
                        continue
                    name_en = str(r.get("name_en", "")).strip()
                    name_ko = str(r.get("name_ko", "")).strip() if "name_ko" in r else ""
                    battery = str(r.get("battery_related", "0")).strip() in ("1", "Y", "y", "yes")
                    rows.append({"cas": cas, "name_en": name_en, "name_ko": name_ko or None, "battery_related": battery})
                return rows
            except Exception as e:
                logger.warning("Excel 로드 실패: %s", e)
    return load_substances_from_csv(BATTERY_CSV)


def merge_battery_substances(base: list[dict], battery_path: Path = BATTERY_CSV) -> list[dict]:
    """베이스에 배터리 물질 추가."""
    if not battery_path.exists():
        return base
    battery_list = load_substances_from_csv(battery_path)
    cas_set = {r["cas"] for r in base}
    for r in battery_list:
        if r["cas"] not in cas_set:
            r["battery_related"] = True
            base.append(r)
            cas_set.add(r["cas"])
    return base


def _format_duration(seconds: float) -> str:
    s = int(round(seconds))
    if s < 60:
        return f"0:{s:02d}"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}:{s:02d}"
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}"


def run_mapping(
    input_path: Path | None = None,
    output_path: Path | None = None,
    stage: int = 3,
    delay_seconds: float = 0.5,
) -> Path:
    """매핑 실행 → Excel 저장."""
    base = load_base_substances(input_path)
    base = merge_battery_substances(base)
    if not base:
        raise RuntimeError("물질 목록이 비어 있습니다.")
    if stage == 1:
        languages = STAGE_1_LANGUAGES
    elif stage == 2:
        languages = STAGE_1_LANGUAGES + STAGE_2_LANGUAGES
    else:
        languages = ALL_LANGUAGES
    total_calls = len(base) * len(languages)
    start = time.perf_counter()
    lang_results = {}
    for idx, sub in enumerate(base):
        cas = sub.get("cas", "")
        name_en = sub.get("name_en", "") or ""
        name_ko = sub.get("name_ko", "") or ""
        for lang_code, lang_label in languages:
            data = get_names_for_language(cas, name_en, name_ko, lang_code, lang_label)
            data["status"] = validate_substance(cas, name_en, lang_code, data.get("name", ""), data.get("synonyms", []))
            lang_results[(cas, lang_code)] = data
            time.sleep(delay_seconds)
        done = (idx + 1) * len(languages)
        elapsed = time.perf_counter() - start
        pct = (done / total_calls * 100) if total_calls else 0
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total_calls - done) / rate if rate > 0 else 0
        logger.info("[%5.1f%%] %d/%d 물질 | 경과 %s | 남은 약 %s", pct, idx + 1, len(base), _format_duration(elapsed), _format_duration(eta))
    substances_for_excel = [{"cas": s["cas"], "ec_number": "", "battery_related": s.get("battery_related", False)} for s in base]
    rows = build_rows(substances_for_excel, lang_results)
    out_path = output_path or (DATA_DIR / f"mapping_{time.strftime('%Y%m%d_%H%M')}.xlsx")
    write_excel(rows, out_path)
    logger.info("저장: %s (행 수: %d)", out_path, len(rows))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="환경 데이터 다국어·배터리 매핑 (ExaOne → Excel)")
    parser.add_argument("--input", type=Path, default=None, help="베이스 물질 CSV/Excel 경로")
    parser.add_argument("--output", type=Path, default=None, help="출력 Excel 경로")
    parser.add_argument("--stage", type=int, default=3, choices=(1, 2, 3), help="언어 단계 (1~3)")
    parser.add_argument("--delay", type=float, default=0.5, help="ExaOne 호출 간 대기(초)")
    args = parser.parse_args()
    run_mapping(input_path=args.input, output_path=args.output, stage=args.stage, delay_seconds=args.delay)


if __name__ == "__main__":
    main()
