"""
ESG 전력·손실량·폐기물 더미 데이터셋 생성.

env_mapping 기준으로 2년치 17~18만 건(정상 92~95%, 이상 5~8%) 생성.
전략: docs/esg-exaone-learning-final-strategy.md

실행 (반드시 app 디렉터리에서):
  cd C:\\dev\\RAG\\app
  python -m training.pipelines.esg_dummy.run_generate_measurements --dry-run
  python -m training.pipelines.esg_dummy.run_generate_measurements --years 2
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_esg_dummy_dir, get_env_mapping_data_dir  # type: ignore  # noqa: E402


# esg-dummy-data-strategy 프로파일 (시드). README·env_mapping/profile_source.json에서 보강.
# 5 process × 2 line = 10 (process, line) → 1h×10×24×365×2 ≈ 17.5만 건
DEFAULT_PROFILE = {
    "process_line": [
        {"process": "mixing", "line": "L1", "rated_kw": 600, "usage_day": [350, 500], "usage_night": [60, 100], "production": [80, 120], "equipment_ct": [4, 6], "scrap": [2, 8], "waste": [1, 4]},
        {"process": "mixing", "line": "L2", "rated_kw": 600, "usage_day": [340, 490], "usage_night": [55, 95], "production": [75, 115], "equipment_ct": [4, 6], "scrap": [2, 8], "waste": [1, 4]},
        {"process": "plate", "line": "L1", "rated_kw": 500, "usage_day": [280, 420], "usage_night": [50, 80], "production": [100, 150], "equipment_ct": [3, 5], "scrap": [2, 6], "waste": [1, 3]},
        {"process": "plate", "line": "L2", "rated_kw": 500, "usage_day": [270, 410], "usage_night": [48, 78], "production": [95, 145], "equipment_ct": [3, 5], "scrap": [2, 6], "waste": [1, 3]},
        {"process": "cell", "line": "L1", "rated_kw": 700, "usage_day": [390, 590], "usage_night": [65, 115], "production": [58, 98], "equipment_ct": [5, 8], "scrap": [1, 5], "waste": [1, 3]},
        {"process": "cell", "line": "L2", "rated_kw": 700, "usage_day": [400, 600], "usage_night": [70, 120], "production": [60, 100], "equipment_ct": [5, 8], "scrap": [1, 5], "waste": [1, 3]},
        {"process": "module", "line": "L1", "rated_kw": 550, "usage_day": [300, 450], "usage_night": [40, 70], "production": [40, 70], "equipment_ct": [3, 5], "scrap": [1, 4], "waste": [0, 2]},
        {"process": "module", "line": "L2", "rated_kw": 550, "usage_day": [290, 440], "usage_night": [38, 68], "production": [38, 68], "equipment_ct": [3, 5], "scrap": [1, 4], "waste": [0, 2]},
        {"process": "pack", "line": "L1", "rated_kw": 450, "usage_day": [250, 380], "usage_night": [30, 60], "production": [30, 50], "equipment_ct": [2, 4], "scrap": [0, 3], "waste": [0, 2]},
        {"process": "pack", "line": "L2", "rated_kw": 450, "usage_day": [240, 370], "usage_night": [28, 58], "production": [28, 48], "equipment_ct": [2, 4], "scrap": [0, 3], "waste": [0, 2]},
    ],
    "contract_kwh_per_hour": 5500,  # 정상 최대 합계(≈4,650 kW) × 1.18. PDF 파싱 성공 시 덮어씀.
    "rule4_usage_per_production_max": 39.8,  # CATL 34.565 × 1.15. README_ESG_Rule_및_설비기준 §2 §4-2 참고.
    "rule5_usage_per_equipment_max": 95,
    "shift_day_start_hour": 6,
    "shift_day_end_hour": 18,
}

ERROR_TYPES = (
    "NEGATIVE_POWER",
    "RATED_EXCEED",
    "CONTRACT_EXCEED",
    "PRODUCTION_RATIO",
    "EQUIPMENT_RATIO",
    "SHIFT_RANGE",
)

# Rule로는 안 잡히는 다변량만 이상 (원인 미상/복합 이상). measurements에는 넣지 않고 validation 로그만.
# 기준: profile의 Rule4/Rule5 상한·공정별 usage/production/scrap/waste 범위를 사용 (임의 0.98·2.5배 등 최소화).
MULTIVARIATE_ANOMALY_TYPES = (
    "MULTIVARIATE_EFFICIENCY_DROP",   # 생산 정상 대비 usage/production이 Rule4 직전(고비율) 구간
    "MULTIVARIATE_IDLE_POWER",         # 생산은 하위권인데 전력은 shift 정상대역 → 대기전력 뉘앙스
    "MULTIVARIATE_SINGLE_EQUIPMENT_LOW",  # 가동 대수 많은데 대당 전력은 Rule5 하위권(병목/부분가동)
    "MULTIVARIATE_BASE_LOAD",          # 생산 0, 전력은 야간(또는 주간) 정상 하한 대비 상승
    "MULTIVARIATE_SCRAP_WASTE_DEVIATION",  # 전력·생산 정상, 프로파일 scrap/waste 상한 대비 초과
)


def _fmt_elapsed(sec: float) -> str:
    """경과 시간을 'N분 M초' 또는 'N시간 M분' 형식으로."""
    if sec < 60:
        return f"{sec:.1f}초"
    if sec < 3600:
        return f"{int(sec // 60)}분 {int(sec % 60)}초"
    return f"{int(sec // 3600)}시간 {int((sec % 3600) // 60)}분"


def _fmt_remaining(sec: float) -> str:
    """남은 시간을 '약 N분' 또는 '약 N초' 형식으로."""
    if sec <= 0:
        return "곧 완료"
    if sec < 60:
        return f"약 {sec:.0f}초"
    if sec < 3600:
        return f"약 {int(sec // 60)}분"
    return f"약 {int(sec // 3600)}시간 {int((sec % 3600) // 60)}분"


def _load_csv_with_encoding(path: Path) -> list[list[str]]:
    for enc in ("utf-8", "cp949", "utf-8-sig"):
        try:
            with open(path, "r", encoding=enc) as f:
                return list(csv.reader(f))
        except (UnicodeDecodeError, OSError):
            continue
    return []


def load_power_demand_patterns(
    env_mapping_dir: Path,
    use_only_recent_two_years: bool = True,
) -> dict[tuple[str, int], float]:
    """
    전력 수요 CSV 로드 → (날짜, 시간)별 수요 비율 테이블.
    use_only_recent_two_years=True 이면 파일명에 2024 또는 2025가 포함된 CSV만 사용(최근 2년만 참고).
    반환: (date_str "YYYY-MM-DD", hour 1..24) -> 0~1 사이 비율 (해당일 해당시간 / 전체 최대)
    """
    pattern: dict[tuple[str, int], float] = {}
    all_vals: list[float] = []
    for path in sorted(env_mapping_dir.glob("*.csv")):
        if use_only_recent_two_years and "2024" not in path.name and "2025" not in path.name:
            continue
        rows = _load_csv_with_encoding(path)
        if not rows:
            continue
        # 첫 컬럼: 날짜, 나머지 24: 1시~24시
        for r in rows[1:]:
            if len(r) < 25:
                continue
            try:
                date_str = r[0].strip()
                if len(date_str) != 10 or date_str[4] != "-":
                    continue
                for h in range(1, 25):
                    v = float(r[h].strip().replace(",", ""))
                    pattern[(date_str, h)] = v
                    all_vals.append(v)
            except (ValueError, IndexError):
                continue
    if not all_vals:
        # CSV 없거나 파싱 실패 시 균등 비율
        return {}
    max_d = max(all_vals)
    if max_d <= 0:
        return {}
    for k in pattern:
        pattern[k] = pattern[k] / max_d
    return pattern


def build_pattern_table_for_range(
    pattern: dict[tuple[str, int], float],
    start_date: datetime,
    end_date: datetime,
) -> dict[tuple[str, int], float]:
    """기간 내 (date, hour)에 대해 패턴이 있으면 사용, 없으면 월·시간대 평균 비율 추정."""
    out: dict[tuple[str, int], float] = {}
    d = start_date
    while d <= end_date:
        date_str = d.strftime("%Y-%m-%d")
        for hour in range(1, 25):
            key = (date_str, hour)
            if key in pattern:
                out[key] = pattern[key]
            else:
                # 기본: 낮(8~17) 높게, 밤 낮게
                if 8 <= hour <= 17:
                    out[key] = 0.7 + random.uniform(0, 0.25)
                else:
                    out[key] = 0.3 + random.uniform(0, 0.25)
            out[key] = min(1.0, max(0.1, out[key]))
        d += timedelta(days=1)
    return out


def _deep_merge(base: dict, override: dict) -> dict:
    """override 키로 base를 덮어씌움. process_line은 override 있으면 통째로 교체."""
    out = dict(base)
    for k, v in override.items():
        if k == "process_line" and isinstance(v, list):
            out[k] = list(v)
        elif isinstance(v, dict) and k in out and isinstance(out[k], dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# MDPI 2025 보조자료 s1 페이지 (Environments 12, 24). 여기서 .xlsx 링크 추출 후 다운로드.
_MDPI_S1_URL = "https://www.mdpi.com/article/10.3390/environments12010024/s1"


def _get_mdpi_dir(env_mapping_dir: Path) -> Path | None:
    """env_mapping 내 MDPI 보조자료 폴더. mdpI(대문자 I) 또는 mdpl(소문자 L) 둘 다 허용."""
    for name in ("mdpI", "mdpl"):
        d = env_mapping_dir / name
        if d.is_dir():
            return d
    return None


def _fetch_mdpi_s1_xlsx(env_mapping_dir: Path) -> bool:
    """외국 자료 가져오기: MDPI s1 페이지 HTML에서 .xlsx 링크를 찾아 다운로드. 성공 시 True."""
    mdpI_dir = env_mapping_dir / "mdpI"  # 새로 만들 때는 mdpI 사용
    mdpI_dir.mkdir(parents=True, exist_ok=True)
    try:
        req = Request(_MDPI_S1_URL, headers={"User-Agent": "Mozilla/5.0 (compatible; ESG-dummy/1.0)"})
        with urlopen(req, timeout=15) as resp:  # noqa: S310
            html = resp.read().decode("utf-8", errors="replace")
        # href=".../file.xlsx" 또는 href="/files/...xlsx" 형태 검색
        m = re.search(r'href\s*=\s*["\']([^"\']*\.xlsx)["\']', html, re.I)
        if not m:
            return False
        link = m.group(1).strip()
        if link.startswith("//"):
            link = "https:" + link
        elif link.startswith("/"):
            link = "https://www.mdpi.com" + link
        elif not link.startswith("http"):
            link = "https://www.mdpi.com/" + link.lstrip("/")
        dest = mdpI_dir / "Battery_factories_impact.xlsx"
        urlretrieve(link, dest)  # noqa: S310
        if dest.stat().st_size > 0:
            print(f"[INFO] mdpI: MDPI s1 페이지에서 다운로드 → {dest.name}")
            return True
    except Exception as e:
        print(f"[WARN] mdpI MDPI s1 자동 다운로드 실패: {e}")
    return False


def _ensure_mdpi_fetched(env_mapping_dir: Path) -> None:
    """데이터셋 없는 부분 가져오기: mdpI가 비어 있으면 (1) MDPI s1 페이지에서 .xlsx 자동 다운로드 시도,
    (2) 실패 시 mdpI_fetch_url.txt에 적힌 URL로 다운로드."""
    existing = _get_mdpi_dir(env_mapping_dir)
    if existing is not None and list(existing.glob("*.xlsx")):
        return
    if _fetch_mdpi_s1_xlsx(env_mapping_dir):
        return
    url_file = env_mapping_dir / "mdpI_fetch_url.txt"
    if not url_file.exists():
        return
    try:
        url = url_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if not url or not url.startswith("http"):
            return
        mdpI_dir = env_mapping_dir / "mdpI"
        mdpI_dir.mkdir(parents=True, exist_ok=True)
        dest = mdpI_dir / "Battery_factories_impact.xlsx"
        urlretrieve(url, dest)  # noqa: S310
        print(f"[INFO] mdpI: mdpI_fetch_url.txt에서 다운로드 → {dest.name}")
    except Exception as e:
        print(f"[WARN] mdpI fetch failed: {e}")


def _load_mdpi_profile_overrides(env_mapping_dir: Path) -> dict:
    """env_mapping/mdpI/*.xlsx(MDPI 2025 보조자료)에서 Rule 4용 에너지 소비(kWh/kWh) 값 추출.

    파싱 전략:
    - Factories_sum 시트의 'Energy consumption' 행에서 kWh/kWh 단위 수치만 읽음.
    - 단위 셀이 'kWh/kWh'인 행의 숫자만 후보로 사용 → 용량(GWh/year) 등 다른 단위 혼입 방지.
    - 단위 셀 파싱 실패 시 폴백: 20~40 범위 숫자만 후보로 제한 (기존 25~50보다 좁혀서 40 GWh 혼입 차단).
    - 성공 시 최댓값 × 1.15를 rule4_usage_per_production_max로 반환.

    오파싱 이력:
    - 기존 코드는 25~50 범위 숫자를 무차별 스캔 → CATL 용량 40 GWh/year가 혼입되어
      40 × 1.15 = 46.0으로 잘못 설정됨. (README_ESG_Rule_및_설비기준.md §2 §4-2 참고)
    - 올바른 값: 34.565(CATL) × 1.15 = 39.8
    """
    overrides: dict = {}
    mdpI_dir = _get_mdpi_dir(env_mapping_dir)
    if mdpI_dir is None:
        return overrides
    xlsx_list = sorted(mdpI_dir.glob("*.xlsx"))
    if not xlsx_list:
        return overrides
    try:
        import pandas as pd  # noqa: I001
    except ImportError:
        return overrides

    for path in xlsx_list[:2]:
        try:
            # Factories_sum 시트 우선, 없으면 첫 번째 시트
            xl = pd.ExcelFile(path, engine="openpyxl")
            sheet = "Factories_sum" if "Factories_sum" in xl.sheet_names else xl.sheet_names[0]
            df = pd.read_excel(xl, sheet_name=sheet, header=None)

            energy_vals: list[float] = []

            # 1순위: 'Energy consumption' 레이블 행에서 단위가 'kWh/kWh'인 행의 숫자만 추출
            for idx, row in df.iterrows():
                row_strs = [str(v).strip() for v in row if not pd.isna(v)]
                label = row_strs[0].lower() if row_strs else ""
                if "energy consumption" not in label and "energy use" not in label:
                    continue
                # 단위 셀이 kWh/kWh 계열인지 확인
                unit_cells = [s for s in row_strs if "kwh" in s.lower()]
                if not any("kwh/kwh" in u.lower() or "kwh/kwh" in u.lower() for u in unit_cells):
                    # 단위 셀 없으면 숫자만 보되 20~40 범위로 제한
                    for v in row:
                        if pd.isna(v):
                            continue
                        try:
                            x = float(v)
                            if 20.0 <= x <= 40.0:
                                energy_vals.append(x)
                        except (TypeError, ValueError):
                            continue
                else:
                    for v in row:
                        if pd.isna(v):
                            continue
                        try:
                            x = float(v)
                            if 20.0 <= x <= 40.0:
                                energy_vals.append(x)
                        except (TypeError, ValueError):
                            continue

            # 2순위: 1순위 실패 시 전체 시트에서 20~40 범위 숫자만 (40 GWh 혼입 차단)
            if not energy_vals:
                for _, row in df.iterrows():
                    for v in row:
                        if pd.isna(v):
                            continue
                        try:
                            x = float(v)
                            if 20.0 <= x <= 40.0:
                                energy_vals.append(x)
                        except (TypeError, ValueError):
                            continue

            if energy_vals:
                max_kwh = max(energy_vals)
                overrides["rule4_usage_per_production_max"] = round(max_kwh * 1.15, 1)
                print(f"[INFO] mdpI: {path.name} ({sheet}) → 에너지 소비 후보 {energy_vals} → 최댓값 {max_kwh} × 1.15 = {overrides['rule4_usage_per_production_max']}")
                break
        except Exception as e:
            print(f"[WARN] mdpI {path.name} read failed: {e}")
    return overrides


def _parse_pct_range(s: str) -> tuple[float, float] | None:
    """'2~5%' 또는 '0.5~1.5%' -> (2, 5) 또는 (0.5, 1.5)."""
    s = s.strip()
    m = re.match(r"([\d.]+)\s*~\s*([\d.]+)\s*%?", s)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    return None


def _load_rule4_from_readme_rated(env_mapping_dir: Path) -> dict:
    """README_ESG_Rule_및_설비기준.md(§2 설비·Rule4 출처)에서 Rule 4 threshold를 파싱해 반환.

    파싱 우선순위:
    1. README §4-2 명시값 블록: `RULE4_THRESHOLD_KWH_PER_KWH = <숫자>` → 그 값을 그대로 사용.
       (엑셀 오파싱 방지를 위해 README에 명시한 확정값. 근거: CATL 34.565 × 1.15 = 39.8)
    2. 폴백: 기존 방식 — "28.3~34.6" 패턴 → 34.6 × 1.15, "30–35" 패턴 → 35 × 1.15.

    mdpI 엑셀 파싱이 성공한 경우 이 함수 결과는 build_profile()에서 무시됨(엑셀 우선).
    반환: {} 또는 {"rule4_usage_per_production_max": float}
    """
    path = env_mapping_dir / "README_ESG_Rule_및_설비기준.md"
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    # 1순위: 명시값 블록 `RULE4_THRESHOLD_KWH_PER_KWH = 39.8`
    m = re.search(r"RULE4_THRESHOLD_KWH_PER_KWH\s*=\s*([\d.]+)", text)
    if m:
        val = round(float(m.group(1)), 1)
        print(f"[INFO] README_ESG_Rule: RULE4_THRESHOLD_KWH_PER_KWH={val} (명시값 직접 적용)")
        return {"rule4_usage_per_production_max": val}

    # 2순위 폴백: 범위 패턴
    m = re.search(r"28\.3\s*[~\-–]\s*34\.6", text)
    if m:
        val = round(34.6 * 1.15, 1)
        print(f"[INFO] README_ESG_Rule: 28.3~34.6 패턴 → rule4_usage_per_production_max={val}")
        return {"rule4_usage_per_production_max": val}
    m = re.search(r"30\s*[~\-–]\s*35", text)
    if m:
        val = round(35 * 1.15, 1)
        print(f"[INFO] README_ESG_Rule: 30~35 패턴 → rule4_usage_per_production_max={val}")
        return {"rule4_usage_per_production_max": val}
    return {}


def _load_scrap_waste_reference_from_readme(env_mapping_dir: Path) -> dict[str, dict]:
    """README_배터리_손실량_폐기물_통상참고치.md §3.2 공정별 표에서 scrap/waste 비율(%) 가져오기.
    반환: { process: { "scrap_pct": (lo, hi), "waste_pct": (lo, hi) }, ... }"""
    path = env_mapping_dir / "README_배터리_손실량_폐기물_통상참고치.md"
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    # §3.2 표: | **mixing** | 2~5% | 0.5~1.5% | ...
    for process in ("mixing", "plate", "cell", "module", "pack"):
        pat = r"\|\s*\*\*" + re.escape(process) + r"\*\*[^|]*\|\s*([\d.~%\s]+)\|\s*([\d.~%\s]+)"
        m = re.search(pat, text)
        if not m:
            continue
        scrap_pct = _parse_pct_range(m.group(1))
        waste_pct = _parse_pct_range(m.group(2))
        if scrap_pct and waste_pct:
            out[process] = {"scrap_pct": scrap_pct, "waste_pct": waste_pct}
    if out:
        print(f"[INFO] README 통상참고치: {list(out.keys())} 공정 scrap/waste 비율 반영")
    return out


def _parse_effective_date_from_tariff_filename(name: str) -> tuple[int, int, int] | None:
    """파일명에서 시행일 추출. 예: 2025년도+4월+1일+시행 → (2025, 4, 1). 실패 시 None."""
    # 2025년도+01월+01일+시행, 2025년도+4월+1일+시행 등
    m = re.search(r"(\d{4})년도\s*\+\s*(\d{1,2})월\s*\+\s*(\d{1,2})일\s*\+\s*시행", name)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"(\d{4})년도\+(\d{1,2})월\+(\d{1,2})일\+시행", name)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # 20210101(high).pdf, 20230101(total).pdf
    m = re.match(r"(\d{4})(\d{2})(\d{2})", name)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # 24.04.01_kepco..., 23.05.16+전력_요금표
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{2})", name)
    if m:
        y = int(m.group(1))
        return (2000 + y if y < 50 else 1900 + y, int(m.group(2)), int(m.group(3)))
    return None


def _is_tariff_or_power_pdf(name: str) -> bool:
    """전기요금·전력 요금·한전 요금표 등 전력 파이프라인에서 훑을 PDF 여부."""
    n = name.lower()
    if "전기요금" in name or "전기요금표" in name:
        return True
    if "전력" in name and "요금표" in name:
        return True
    if "kepco" in n and ("electric" in n or "charges" in n or "요금" in name):
        return True
    if re.match(r"^\d{8}", name):
        return True  # 20210101(high).pdf, 20230101(total).pdf
    if re.match(r"^\d{2}\.\d{2}\.\d{2}", name):
        return True  # 23.05.16+..., 24.04.01_...
    return False


def _list_tariff_pdfs_newest_first(env_mapping_dir: Path) -> list[Path]:
    """env_mapping 내 전기·전력 요금표 PDF 목록을 시행일 기준 최신순으로 반환. (전기요금표, 전력_요금표, kepco, YYYYMMDD 등 전부 포함)"""
    all_pdfs: list[Path] = []
    for p in env_mapping_dir.iterdir():
        if not p.is_file() or p.suffix.lower() != ".pdf":
            continue
        if _is_tariff_or_power_pdf(p.name):
            all_pdfs.append(p)
    dated: list[tuple[tuple[int, int, int], Path]] = []
    for p in all_pdfs:
        d = _parse_effective_date_from_tariff_filename(p.name)
        if d:
            dated.append((d, p))
        else:
            dated.append(((0, 0, 0), p))
    dated.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in dated]


def _list_reference_pdfs(env_mapping_dir: Path, exclude_paths: set[Path]) -> list[Path]:
    """전력 파이프라인에서 '참고 문서'로 훑을 PDF (요금표가 아닌 나머지 + mdpI 내 PDF)."""
    out: list[Path] = []
    for p in env_mapping_dir.iterdir():
        if not p.is_file() or p.suffix.lower() != ".pdf":
            continue
        if p in exclude_paths:
            continue
        out.append(p)
    mdpI = _get_mdpi_dir(env_mapping_dir)
    if mdpI is not None:
        for p in mdpI.iterdir():
            if p.is_file() and p.suffix.lower() == ".pdf":
                out.append(p)
    return sorted(out, key=lambda x: x.name)


def _parse_contract_kw_from_text(text: str) -> tuple[list[int], int | None]:
    """텍스트에서 계약 전력 후보 추출. (candidates_kw, chosen_kw)

    선택 기준:
    - 전기요금표는 요금 단가 구간 구분(1,000 kW 미만/이상)만 있고,
      실제 공장 계약 전력 상한은 공장 규모에 따라 개별 계약값임.
    - 더미 공장 정상 최대 합계 ≈ 4,650 kW 기준으로,
      계약 전력은 그보다 10~20% 높은 5,000~5,500 kW가 현실적.
    - PDF에서 1,000~10,000 kW 구간 숫자 중 공장 규모에 가장 가까운 값을 선택.
      후보가 없으면 None 반환 → DEFAULT_PROFILE 기본값(5,500) 사용.
    """
    numbers: list[int] = []
    # "계약전력 X kW" 패턴 우선 추출
    for m in re.finditer(r"(?:계약\s*전력|계약전력)[^\d]*(\d{1,3}(?:,\d{3})*)", text):
        raw = m.group(1).replace(",", "")
        n = int(raw)
        if 1000 <= n <= 10000:
            numbers.append(n)
    # 일반 kW 숫자 (1,000~10,000 범위만)
    for m in re.finditer(r"(\d{1,3}(?:,\d{3})*)\s*kW", text):
        raw = m.group(1).replace(",", "")
        n = int(raw)
        if 1000 <= n <= 10000:
            numbers.append(n)
    if not numbers:
        return ([], None)
    cand = sorted(set(numbers))
    # 공장 정상 최대 합계(≈4,650 kW) 기준으로 가장 가까운 상위 값 선택
    # 5,000~6,000 kW 구간 우선, 없으면 4,500~7,000, 없으면 최솟값
    target = 5500
    preferred = [n for n in cand if 5000 <= n <= 6000]
    if preferred:
        chosen = min(preferred, key=lambda x: abs(x - target))
    else:
        fallback = [n for n in cand if 4500 <= n <= 7000]
        chosen = min(fallback, key=lambda x: abs(x - target)) if fallback else min(cand)
    return (cand, chosen)


def _load_contract_kwh_from_tariff_pdf(env_mapping_dir: Path) -> dict:
    """
    env_mapping 내 전력 관련 PDF 전부 훑기: 요금표는 계약 전력 파싱, 나머지는 참고 문서로 기록.
    시행일 최신 1건을 Rule 3 기준으로 사용.
    반환: {"chosen_kw", "candidates_kw", "source_pdf", "error", "history"}
    history: 요금표 파싱 결과 + 참고 문서( KCI, mdpI/Supplementary 등) 훑은 이력.
    """
    result: dict = {"chosen_kw": None, "candidates_kw": [], "source_pdf": None, "error": None, "history": []}
    sorted_pdfs = _list_tariff_pdfs_newest_first(env_mapping_dir)
    try:
        from domain.shared.document_extract import extract_text_from_document  # type: ignore
    except ImportError:
        result["error"] = "PDF 추출 모듈 없음"
        return result
    tariff_paths = set(sorted_pdfs)
    for pdf_path in sorted_pdfs:
        effective_ymd = _parse_effective_date_from_tariff_filename(pdf_path.name)
        entry: dict = {
            "source_pdf": pdf_path.name,
            "effective_ymd": (f"{effective_ymd[0]}-{effective_ymd[1]:02d}-{effective_ymd[2]:02d}" if effective_ymd and effective_ymd != (0, 0, 0) else None),
            "candidates_kw": [],
            "chosen_kw": None,
            "error": None,
            "note": None,
        }
        try:
            text = extract_text_from_document(path=pdf_path)
            cand, chosen = _parse_contract_kw_from_text(text)
            entry["candidates_kw"] = cand
            entry["chosen_kw"] = chosen
            if not cand:
                entry["error"] = "계약 전력으로 추정되는 숫자 없음"
        except Exception as e:
            entry["error"] = str(e)
        result["history"].append(entry)
        if result["chosen_kw"] is None and entry.get("chosen_kw") is not None:
            result["chosen_kw"] = entry["chosen_kw"]
            result["candidates_kw"] = entry.get("candidates_kw", [])
            result["source_pdf"] = entry["source_pdf"]
    if not sorted_pdfs:
        result["error"] = "전기·전력 요금표 PDF 없음"
    elif result["chosen_kw"] is None and result["history"]:
        result["error"] = "모든 요금표 PDF에서 계약 전력 파싱 실패"
    # 참고 문서(KCI, mdpI/Supplementary 등)도 전력 파이프라인에서 한 번 훑기
    reference_pdfs = _list_reference_pdfs(env_mapping_dir, tariff_paths)
    for pdf_path in reference_pdfs:
        entry = {
            "source_pdf": pdf_path.name,
            "effective_ymd": None,
            "candidates_kw": [],
            "chosen_kw": None,
            "error": None,
            "note": "참고 문서 (계약 전력 파싱 미적용)",
        }
        try:
            text = extract_text_from_document(path=pdf_path)
            entry["text_length"] = len(text)
        except Exception as e:
            entry["error"] = str(e)
        result["history"].append(entry)
    return result


def build_profile(env_mapping_dir: Path, out_dir: Path, dry_run: bool) -> dict:
    """env_mapping/profile_source.json, 전기요금표 PDF, mdpI 엑셀, README 통상참고치로 프로파일 구성 후 profile.json 저장."""
    _ensure_mdpi_fetched(env_mapping_dir)
    profile = dict(DEFAULT_PROFILE)
    source_path = env_mapping_dir / "profile_source.json"
    if source_path.exists():
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                override = json.load(f)
            profile = _deep_merge(profile, override)
            print(f"[INFO] profile merged from {source_path}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] profile_source.json load failed: {e}, using DEFAULT_PROFILE")
    # 전기요금표 PDF 전부 훑기(예측용 이력) + 시행일 최신 1건을 Rule 3 기준으로 사용
    pdf_result = _load_contract_kwh_from_tariff_pdf(env_mapping_dir)
    history = pdf_result.get("history") or []
    if history:
        print(f"[INFO] env_mapping PDF {len(history)}건 훑음 (요금표 시행일 최신순 + 참고 문서). Rule 3 기준(최신 요금표): {history[0].get('source_pdf')}")
    if pdf_result.get("chosen_kw") is not None:
        profile["contract_kwh_per_hour"] = pdf_result["chosen_kw"]
        cand = pdf_result.get("candidates_kw") or []
        print(f"[INFO] Rule 3 기준: 발견된 후보(kW) {cand} → 적용값 {pdf_result['chosen_kw']} kW (최신 시행 PDF)")
        print(f"       검증: PDF({pdf_result.get('source_pdf')})와 대조하여 적용값이 계약 전력 상한인지 확인하세요.")
    elif pdf_result.get("error"):
        print(f"[INFO] 전기요금표 PDF 미사용: {pdf_result['error']} — profile_source 또는 기본값 사용")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        parse_result_path = out_dir / "tariff_contract_parse_result.json"
        write_result = {
            "source_pdf": pdf_result.get("source_pdf"),
            "candidates_kw": pdf_result.get("candidates_kw", []),
            "chosen_kw": pdf_result.get("chosen_kw"),
            "error": pdf_result.get("error"),
            "note": "파싱 검증용: PDF와 대조하여 chosen_kw가 계약 전력 상한인지 확인. 이상 시 profile_source.json에 contract_kwh_per_hour를 직접 설정하세요.",
        }
        with open(parse_result_path, "w", encoding="utf-8") as f:
            json.dump(write_result, f, ensure_ascii=False, indent=2)
        # 예측용: 시행일별 파싱 이력 + 참고 PDF + README 훑은 목록 (env_mapping 전부 사용)
        history_path = out_dir / "tariff_contract_history.json"
        readmes_scanned = []
        for p in sorted(env_mapping_dir.iterdir()):
            if p.is_file() and p.suffix.lower() == ".md" and p.name.upper().startswith("README"):
                readmes_scanned.append({"name": p.name, "size": p.stat().st_size})
        history_export = {
            "note": "예측·이력용. env_mapping 내 전기·전력 요금표 PDF + 참고 PDF(KCI, mdpI 등) + README 훑은 결과.",
            "history": history,
            "readmes_scanned": readmes_scanned,
        }
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history_export, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
    mdpi_overrides = _load_mdpi_profile_overrides(env_mapping_dir)
    if mdpi_overrides:
        profile = _deep_merge(profile, mdpi_overrides)
    readme_rated = _load_rule4_from_readme_rated(env_mapping_dir)
    if readme_rated and "rule4_usage_per_production_max" not in mdpi_overrides:
        profile = _deep_merge(profile, readme_rated)
        print("[INFO] README_ESG_Rule: rule4_usage_per_production_max 반영 (README_ESG_Rule_및_설비기준.md)")
    readme_ref = _load_scrap_waste_reference_from_readme(env_mapping_dir)
    if readme_ref:
        new_pl: list[dict] = []
        for pl in profile["process_line"]:
            ref = readme_ref.get(pl["process"])
            if ref:
                p_lo, p_hi = pl["production"][0], pl["production"][1]
                s_lo, s_hi = ref["scrap_pct"][0] / 100, ref["scrap_pct"][1] / 100
                w_lo, w_hi = ref["waste_pct"][0] / 100, ref["waste_pct"][1] / 100
                new_pl.append({
                    **pl,
                    "scrap": [round(p_lo * s_lo, 1), round(p_hi * s_hi, 1)],
                    "waste": [round(p_lo * w_lo, 1), round(p_hi * w_hi, 1)],
                })
            else:
                new_pl.append(dict(pl))
        profile["process_line"] = new_pl
    profile_path = out_dir / "profile.json"
    if dry_run:
        print(f"[DRY-RUN] would write profile to {profile_path} (process_line={len(profile['process_line'])} entries)")
        return profile
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    print(f"[INFO] profile saved: {profile_path}")
    return profile


def _is_day_shift(hour: int, profile: dict) -> bool:
    start = profile.get("shift_day_start_hour", 6)
    end = profile.get("shift_day_end_hour", 18)
    return start <= hour < end


def _sample_range(lo: int | float, hi: int | float) -> float:
    return lo + random.random() * (hi - lo)


def generate_normal_row(
    noticedate: str,
    hour: int,
    pl: dict,
    profile: dict,
    pattern_ratio: float,
    share: float,
    contract_total: float,
) -> dict:
    """프로파일 + 패턴 비율로 정상 행 1건 생성. usage는 share로 계약 합계 내에서 배분."""
    is_day = _is_day_shift(hour, profile)
    if is_day:
        u_lo, u_hi = pl["usage_day"][0], pl["usage_day"][1]
    else:
        u_lo, u_hi = pl["usage_night"][0], pl["usage_night"][1]
    # 해당 행이 받을 usage 상한: contract_total * share. 범위 안에서 패턴 반영
    u_target = contract_total * share * (0.8 + 0.2 * pattern_ratio)
    u_target = min(u_hi, max(u_lo, u_target))
    usage = round(_sample_range(u_lo, min(u_hi, u_target + (u_hi - u_lo) * 0.2)), 2)
    production = round(_sample_range(pl["production"][0], pl["production"][1]), 2)
    equipment_ct = random.randint(pl["equipment_ct"][0], pl["equipment_ct"][1])
    # 정상 행은 Rule 4·5 만족: usage <= production*rule4_max, usage <= equipment_ct*rule5_max
    rule4_max = profile.get("rule4_usage_per_production_max", 7.0)
    rule5_max = profile.get("rule5_usage_per_equipment_max", 95)
    cap4 = production * rule4_max
    cap5 = equipment_ct * rule5_max
    usage = min(usage, cap4, cap5)
    usage = max(u_lo, usage)
    # u_lo가 cap 초과일 수 있으므로 cap 재적용 후 반올림
    usage = min(usage, cap4, cap5)
    usage = round(usage, 2)
    if equipment_ct > 0 and usage / equipment_ct > rule5_max:
        usage = round(equipment_ct * rule5_max - 0.01, 2)
    if production > 0 and usage / production > rule4_max:
        usage = round(production * rule4_max - 0.01, 2)
    scrap = round(_sample_range(pl["scrap"][0], pl["scrap"][1]), 2)
    waste = round(_sample_range(pl["waste"][0], pl["waste"][1]), 2)
    shift = "day" if is_day else "night"
    return {
        "noticedate": noticedate,
        "process": pl["process"],
        "line": pl["line"],
        "usage": usage,
        "production": production,
        "equipment_ct": equipment_ct,
        "shift": shift,
        "scrap": scrap,
        "waste": waste,
    }


def generate_anomaly_row_and_validation(
    noticedate: str,
    hour: int,
    pl: dict,
    profile: dict,
    rule_id: int,
    row_number: int,
) -> tuple[dict, dict]:
    """Rule 1~6 중 하나에 걸리도록 행 + validation 로그 생성."""
    is_day = _is_day_shift(hour, profile)
    shift = "day" if is_day else "night"
    # 기본값 채우고 rule에 맞게 usage 등 변조
    production = round(_sample_range(pl["production"][0], pl["production"][1]), 2)
    equipment_ct = random.randint(pl["equipment_ct"][0], pl["equipment_ct"][1])
    scrap = round(_sample_range(pl["scrap"][0], pl["scrap"][1]), 2)
    waste = round(_sample_range(pl["waste"][0], pl["waste"][1]), 2)

    if rule_id == 1:
        usage = round(random.uniform(-50, -10), 2)
        val = {"noticedate": noticedate, "process": pl["process"], "line": pl["line"], "usage": usage, "production": production, "equipment_ct": equipment_ct, "shift": shift, "scrap": scrap, "waste": waste}
        log = {"row_number": row_number, "error_type": "NEGATIVE_POWER", "value": usage, "threshold": 0}
    elif rule_id == 2:
        usage = round(pl["rated_kw"] * random.uniform(1.1, 1.3), 2)
        val = {"noticedate": noticedate, "process": pl["process"], "line": pl["line"], "usage": usage, "production": production, "equipment_ct": equipment_ct, "shift": shift, "scrap": scrap, "waste": waste}
        log = {"row_number": row_number, "error_type": "RATED_EXCEED", "value": usage, "threshold": pl["rated_kw"]}
    elif rule_id == 4:
        usage = round(production * profile["rule4_usage_per_production_max"] * random.uniform(1.1, 1.4), 2)
        val = {"noticedate": noticedate, "process": pl["process"], "line": pl["line"], "usage": usage, "production": production, "equipment_ct": equipment_ct, "shift": shift, "scrap": scrap, "waste": waste}
        log = {"row_number": row_number, "error_type": "PRODUCTION_RATIO", "value": round(usage / production, 2), "threshold": profile["rule4_usage_per_production_max"]}
    elif rule_id == 5:
        usage = round(equipment_ct * profile["rule5_usage_per_equipment_max"] * random.uniform(1.1, 1.4), 2)
        val = {"noticedate": noticedate, "process": pl["process"], "line": pl["line"], "usage": usage, "production": production, "equipment_ct": equipment_ct, "shift": shift, "scrap": scrap, "waste": waste}
        log = {"row_number": row_number, "error_type": "EQUIPMENT_RATIO", "value": round(usage / equipment_ct, 2), "threshold": profile["rule5_usage_per_equipment_max"]}
    elif rule_id == 6:
        if is_day:
            usage = round(pl["rated_kw"] * random.uniform(0.95, 1.05), 2)
        else:
            usage = round(_sample_range(pl["usage_day"][0], pl["usage_day"][1]), 2)
        val = {"noticedate": noticedate, "process": pl["process"], "line": pl["line"], "usage": usage, "production": production, "equipment_ct": equipment_ct, "shift": shift, "scrap": scrap, "waste": waste}
        night_hi = pl["usage_night"][1]
        log = {"row_number": row_number, "error_type": "SHIFT_RANGE", "value": usage, "threshold": night_hi}
    else:
        usage = round(_sample_range(pl["usage_day"][0], pl["usage_day"][1]), 2)
        val = {"noticedate": noticedate, "process": pl["process"], "line": pl["line"], "usage": usage, "production": production, "equipment_ct": equipment_ct, "shift": shift, "scrap": scrap, "waste": waste}
        # Rule 3: 동일 시간 합계 초과. value = 해당 시간대 가상 합계
        fake_sum = round(profile["contract_kwh_per_hour"] * random.uniform(1.05, 1.25), 2)
        log = {"row_number": row_number, "error_type": "CONTRACT_EXCEED", "value": fake_sum, "threshold": profile["contract_kwh_per_hour"]}
    return val, log


def _multivariate_row(
    noticedate: str, hour: int, pl: dict, shift: str,
    usage: float, production: float, equipment_ct: int, scrap: float, waste: float,
) -> dict:
    """다변량용 동일 스키마 행 딕셔너리."""
    return {
        "noticedate": noticedate,
        "process": pl["process"],
        "line": pl["line"],
        "usage": usage,
        "production": production,
        "equipment_ct": equipment_ct,
        "shift": shift,
        "scrap": scrap,
        "waste": waste,
    }


def _clip_usage_below_rule45(
    usage: float,
    production: float,
    equipment_ct: int,
    rule4_max: float,
    rule5_max: float,
) -> float:
    """다변량 행은 단일 Rule 4·5 위반으로 분류되지 않게 usage 상한을 살짝 낮춤."""
    u = float(usage)
    margin = 0.05
    if production > 1e-6:
        u = min(u, production * rule4_max - margin)
    if equipment_ct > 0:
        u = min(u, equipment_ct * rule5_max - margin)
    return round(max(u, 0.01), 2)


def generate_multivariate_row_and_validation(
    noticedate: str,
    hour: int,
    pl: dict,
    profile: dict,
    pattern_type: str,
    row_number: int,
) -> tuple[dict, dict]:
    """다변량만 이상: profile Rule4/5·공정 범위 기반. 단일 Rule 위반은 피하고 복합 패턴 라벨용."""
    is_day = _is_day_shift(hour, profile)
    shift = "day" if is_day else "night"
    rule4_max = float(profile.get("rule4_usage_per_production_max", 39.8))
    rule5_max = float(profile.get("rule5_usage_per_equipment_max", 95))
    u_lo, u_hi = (pl["usage_day"][0], pl["usage_day"][1]) if is_day else (pl["usage_night"][0], pl["usage_night"][1])
    p_lo, p_hi = pl["production"][0], pl["production"][1]
    p_span = max(p_hi - p_lo, 1e-6)

    equipment_ct = random.randint(pl["equipment_ct"][0], pl["equipment_ct"][1])
    scrap = round(_sample_range(pl["scrap"][0], pl["scrap"][1]), 2)
    waste = round(_sample_range(pl["waste"][0], pl["waste"][1]), 2)

    if pattern_type == "MULTIVARIATE_EFFICIENCY_DROP":
        # 생산은 중~상위권, usage/production은 Rule4 상한의 93~99.5% (정상 대비 고비율, Rule4 미초과)
        production = round(p_lo + p_span * random.uniform(0.45, 0.95), 2)
        ratio_target = rule4_max * random.uniform(0.93, 0.995)
        usage = round(production * ratio_target, 2)
        usage = _clip_usage_below_rule45(usage, production, equipment_ct, rule4_max, rule5_max)
        ratio = round(usage / production, 2) if production else 0.0
        row = _multivariate_row(noticedate, hour, pl, shift, usage, production, equipment_ct, scrap, waste)
        log = {
            "row_number": row_number,
            "error_type": "MULTIVARIATE_EFFICIENCY_DROP",
            "value": ratio,
            "threshold": f"rule4_cap≈{round(rule4_max, 2)} usage/prod={ratio}",
        }
        return row, log

    if pattern_type == "MULTIVARIATE_IDLE_POWER":
        # 생산 하위 12~30%, 전력은 shift 정상대역 중간~상단 (같은 전력인데 물동량만 적음)
        production = round(p_lo + p_span * random.uniform(0.12, 0.30), 2)
        usage = round(_sample_range((u_lo + u_hi) * 0.45, u_hi), 2)
        usage = _clip_usage_below_rule45(usage, production, equipment_ct, rule4_max, rule5_max)
        row = _multivariate_row(noticedate, hour, pl, shift, usage, production, equipment_ct, scrap, waste)
        log = {
            "row_number": row_number,
            "error_type": "MULTIVARIATE_IDLE_POWER",
            "value": round(usage / production, 2) if production > 1e-6 else 0.0,
            "threshold": f"shift_band={u_lo}~{u_hi} prod_low",
        }
        return row, log

    if pattern_type == "MULTIVARIATE_BASE_LOAD":
        production = 0.0
        # 생산 0일 때: shift별 usage 하한 대비 +8~22% (프로파일 기저 대비 이탈)
        u_base = u_lo + (u_hi - u_lo) * random.uniform(0.15, 0.35)
        usage = round(u_base * random.uniform(1.08, 1.22), 2)
        usage = min(usage, equipment_ct * rule5_max - 0.05) if equipment_ct > 0 else usage
        usage = round(max(usage, 0.01), 2)
        row = _multivariate_row(noticedate, hour, pl, shift, usage, production, equipment_ct, scrap, waste)
        log = {
            "row_number": row_number,
            "error_type": "MULTIVARIATE_BASE_LOAD",
            "value": usage,
            "threshold": f"production=0 rule5_cap≈{equipment_ct * rule5_max:.1f}",
        }
        return row, log

    if pattern_type == "MULTIVARIATE_SINGLE_EQUIPMENT_LOW":
        # 가동 대수는 상위, 대당 전력은 Rule5의 45~70% (부분 부하·병목 뉘앙스, Rule5 미초과)
        equipment_ct = random.randint(
            max(pl["equipment_ct"][0], pl["equipment_ct"][1] - 1),
            pl["equipment_ct"][1],
        )
        production = round(_sample_range(p_lo, p_hi), 2)
        per_eq = rule5_max * random.uniform(0.45, 0.70)
        usage = round(equipment_ct * per_eq, 2)
        usage = _clip_usage_below_rule45(usage, production, equipment_ct, rule4_max, rule5_max)
        row = _multivariate_row(noticedate, hour, pl, shift, usage, production, equipment_ct, scrap, waste)
        log = {
            "row_number": row_number,
            "error_type": "MULTIVARIATE_SINGLE_EQUIPMENT_LOW",
            "value": round(usage / equipment_ct, 2) if equipment_ct else 0.0,
            "threshold": f"rule5_cap={rule5_max} per_eq_low",
        }
        return row, log

    # MULTIVARIATE_SCRAP_WASTE_DEVIATION — 프로파일 상한 대비 +12~38% (통상참고치 초과 수준)
    usage = round(_sample_range(u_lo, u_hi), 2)
    production = round(_sample_range(p_lo, p_hi), 2)
    usage = _clip_usage_below_rule45(usage, production, equipment_ct, rule4_max, rule5_max)
    # 프로파일 상한 대비 비율 초과(통상참고치 이탈 수준). production 대비 물리 상한은 더미에서 생략(라벨 분리 우선).
    scrap = round(pl["scrap"][1] * random.uniform(1.12, 1.38), 2)
    waste = round(pl["waste"][1] * random.uniform(1.10, 1.32), 2)
    row = _multivariate_row(noticedate, hour, pl, shift, usage, production, equipment_ct, scrap, waste)
    log = {
        "row_number": row_number,
        "error_type": "MULTIVARIATE_SCRAP_WASTE_DEVIATION",
        "value": f"scrap={scrap} waste={waste}",
        "threshold": f"scrap_max={pl['scrap'][1]} waste_max={pl['waste'][1]}",
    }
    return row, log


def main() -> None:
    parser = argparse.ArgumentParser(description="ESG 전력·손실량·폐기물 더미 데이터셋 생성")
    parser.add_argument("--years", type=int, default=2, help="생성 기간(년). 기본 2")
    parser.add_argument("--seed", type=int, default=42, help="랜덤 시드")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성 없이 경로·프로파일만 확인")
    parser.add_argument("--anomaly-rate", type=float, default=0.06, help="이상 비율 (기본 0.06 = 6%%)")
    parser.add_argument("--output-labeled", action="store_true", help="학습용 labeled_slots.csv 함께 출력 (전체 슬롯 + label)")
    args = parser.parse_args()

    random.seed(args.seed)
    env_mapping_dir = get_env_mapping_data_dir()
    out_dir = get_esg_dummy_dir()
    print(f"[INFO] env_mapping={env_mapping_dir}, out_dir={out_dir}, years={args.years}")

    profile = build_profile(env_mapping_dir, out_dir, args.dry_run)
    if args.dry_run:
        print("[DRY-RUN] 실제 행 생성은 생략.")
        return

    # 1) 전력 수요 패턴 — 5년치 CSV 전부 참고(예측·계절성용), 생성은 최근 2년(2024~2025)만
    pattern = load_power_demand_patterns(env_mapping_dir, use_only_recent_two_years=False)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024 + args.years - 1, 12, 31)
    print(f"[INFO] 패턴: 5년치 전력 수요 CSV 참고. 생성 기간: {start_date.date()} ~ {end_date.date()} (최근 2년)")
    pattern_table = build_pattern_table_for_range(pattern, start_date, end_date)
    print(f"[INFO] 패턴 테이블: {len(pattern_table)} (date, hour) 개")

    process_line = profile["process_line"]
    contract = profile["contract_kwh_per_hour"]
    n_pl = len(process_line)
    share_per_pl = 1.0 / n_pl

    # 예상 총 슬롯(건) 수: (날짜 수) × 24 × 10(process, line)
    days_count = (end_date - start_date).days + 1
    expected_slots = days_count * 24 * n_pl
    # 순수 Python 생성이라 슬롯당 약 0.01~0.05ms 수준 → 대략 수 초~수십 초
    expected_sec_rough = max(5, expected_slots / 50_000)
    eta_rough = datetime.now() + timedelta(seconds=expected_sec_rough)

    print("=" * 60)
    print("[실행 전] 예상 건수 · 소요 시간 · 완료 예정")
    print("=" * 60)
    print(f"  예상 총 슬롯: {expected_slots:,}건 (날짜 {days_count}일 × 24시간 × {n_pl} (process,line))")
    print(f"  예상 정상 행: 약 {int(expected_slots * (1 - args.anomaly_rate)):,}건 (measurements)")
    print(f"  예상 이상 로그: 약 {int(expected_slots * args.anomaly_rate):,}건 (validation_logs)")
    print(f"  예상 소요: 약 {_fmt_elapsed(expected_sec_rough)} (실제 속도에 따라 변동)")
    print(f"  완료 예정: {eta_rough.strftime('%Y-%m-%d %H:%M')} (현재 {datetime.now().strftime('%H:%M')} 기준)")
    print("=" * 60)
    print("  진행률: 2.5만 건마다 [경과 | 속도 | 남은 시간] 출력")
    print("=" * 60)
    print()

    measurements_rows: list[dict] = []
    validation_rows: list[dict] = []
    labeled_rows: list[dict] = []
    anomaly_row_number = 0

    t_start = time.perf_counter()
    d = start_date
    total_slots = 0
    report_every = 25_000
    while d <= end_date:
        date_str = d.strftime("%Y-%m-%d")
        for hour in range(1, 25):
            key = (date_str, hour)
            pat_ratio = pattern_table.get(key, 0.5)
            target_total = contract * 0.85 * (0.5 + 0.5 * pat_ratio)

            # Rule 3(CONTRACT_EXCEED): 이 시간대 전체 라인을 한꺼번에 이상으로 만들기
            # 전체 라인 합계가 계약 전력을 초과하도록 usage를 부풀려서 생성
            hour_is_contract_anomaly = random.random() < (args.anomaly_rate * 0.15)
            hour_contract_rows: list[dict] = []

            for i, pl in enumerate(process_line):
                total_slots += 1
                if hour_is_contract_anomaly:
                    # Rule 3: 전체 합계가 계약 전력 초과하도록 각 라인 usage를 정상 상한의 1.1~1.3배로 생성
                    anomaly_row_number += 1
                    is_day = _is_day_shift(hour, profile)
                    usage_hi = pl["usage_day"][1] if is_day else pl["usage_night"][1]
                    usage = round(usage_hi * random.uniform(1.1, 1.3), 2)
                    production = round(_sample_range(pl["production"][0], pl["production"][1]), 2)
                    equipment_ct = random.randint(pl["equipment_ct"][0], pl["equipment_ct"][1])
                    scrap = round(_sample_range(pl["scrap"][0], pl["scrap"][1]), 2)
                    waste = round(_sample_range(pl["waste"][0], pl["waste"][1]), 2)
                    shift = "day" if is_day else "night"
                    row = {
                        "noticedate": date_str,
                        "hour": hour,
                        "process": pl["process"],
                        "line": pl["line"],
                        "usage": usage,
                        "production": production,
                        "equipment_ct": equipment_ct,
                        "shift": shift,
                        "scrap": scrap,
                        "waste": waste,
                    }
                    hour_contract_rows.append(row)
                    if args.output_labeled:
                        labeled_rows.append({**row, "label": "CONTRACT_EXCEED"})
                elif random.random() < args.anomaly_rate:
                    anomaly_row_number += 1
                    # 다변량만 이상 2~4% 목표: 이상의 약 35%를 다변량으로 (정상 92~95%, Rule별 0.5~1%, 다변량 2~4%)
                    if random.random() < 0.35:
                        mtype = random.choice(MULTIVARIATE_ANOMALY_TYPES)
                        row, log = generate_multivariate_row_and_validation(date_str, hour, pl, profile, mtype, anomaly_row_number)
                        validation_rows.append(log)
                        if args.output_labeled:
                            labeled_rows.append({**row, "hour": hour, "label": log["error_type"]})
                    else:
                        # Rule 3은 위에서 시간대 단위로 처리하므로 여기서는 1~2, 4~6만
                        rule_id = random.choice([1, 2, 4, 5, 6])
                        val, log = generate_anomaly_row_and_validation(date_str, hour, pl, profile, rule_id, anomaly_row_number)
                        validation_rows.append(log)
                        if args.output_labeled:
                            labeled_rows.append({**val, "hour": hour, "label": log["error_type"]})
                    # 이상 행은 measurements에 넣지 않음
                else:
                    row = generate_normal_row(date_str, hour, pl, profile, pat_ratio, share_per_pl, target_total)
                    # include hour in measurements for hourly aggregation / moving averages
                    row["hour"] = hour
                    measurements_rows.append(row)
                    if args.output_labeled:
                        labeled_rows.append({**row, "hour": hour, "label": "normal"})

                if total_slots % report_every == 0:
                    elapsed = time.perf_counter() - t_start
                    rate = total_slots / elapsed if elapsed > 0 else 0
                    remaining_sec = (expected_slots - total_slots) / rate if rate > 0 else 0
                    print(f"  [진행] {total_slots:,}/{expected_slots:,}  |  경과 {_fmt_elapsed(elapsed)}  |  속도 {rate:,.0f}건/초  |  남은 시간 {_fmt_remaining(remaining_sec)}")

            # Rule 3 CONTRACT_EXCEED: 이 시간대 전체 라인 합계가 계약 전력 초과하는지 확인 후 validation_log 기록
            if hour_is_contract_anomaly and hour_contract_rows:
                hour_total = sum(r["usage"] for r in hour_contract_rows)
                for r in hour_contract_rows:
                    anomaly_row_number += 1
                    log = {
                        "row_number": anomaly_row_number,
                        "error_type": "CONTRACT_EXCEED",
                        "value": round(hour_total, 2),
                        "threshold": profile["contract_kwh_per_hour"],
                    }
                    validation_rows.append(log)
                    # CONTRACT_EXCEED 이상 행은 measurements에 추가 (실제 usage 값이 있는 행)
                    measurements_rows.append(r)

        d = d + timedelta(days=1)

    # CSV 저장
    out_measurements = out_dir / "measurements.csv"
    out_validation = out_dir / "validation_logs.csv"
    cols = ["noticedate", "hour", "process", "line", "usage", "production", "equipment_ct", "shift", "scrap", "waste"]
    with open(out_measurements, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(measurements_rows)
    with open(out_validation, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["row_number", "error_type", "value", "threshold"])
        w.writeheader()
        w.writerows(validation_rows)

    if args.output_labeled and labeled_rows:
        out_labeled = out_dir / "labeled_slots.csv"
        labeled_cols = ["noticedate", "hour", "process", "line", "usage", "production", "equipment_ct", "shift", "scrap", "waste", "label"]
        with open(out_labeled, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=labeled_cols)
            w.writeheader()
            w.writerows(labeled_rows)
        print(f"  labeled_slots: {out_labeled} ({len(labeled_rows):,} rows)")

    t_total = time.perf_counter() - t_start
    rate_final = total_slots / t_total if t_total > 0 else 0
    print()
    print("=" * 60)
    print("[완료] 최종 요약")
    print("=" * 60)
    print(f"  measurements: {out_measurements} ({len(measurements_rows):,} rows)")
    print(f"  validation_logs: {out_validation} ({len(validation_rows):,} rows)")
    print(f"  총 슬롯: {total_slots:,}건  |  총 소요: {_fmt_elapsed(t_total)}  |  속도: {rate_final:,.0f}건/초")
    print("=" * 60)


if __name__ == "__main__":
    main()
