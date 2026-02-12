"""
O*NET xlsx 추출 전략 — competency_anchors 통합 스키마.

Abilities / Task Statements / Technology Skills / Work Styles 4종을
content, category, level, section_title, source, source_type, metadata 로 변환.
의존성: pandas, openpyxl (requirements.txt).
"""

from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore

from domain.shared.strategies.excel_strategy import ExcelExtractStrategy  # type: ignore

SOURCE_TYPE_LITERAL = "ONET"


def _row_to_anchor(
    content: str,
    category: str,
    section_title: str,
    source: str,
    level: int | float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not content or not content.strip():
        content = "(no text)"
    return {
        "content": content.strip(),
        "category": category,
        "level": level,
        "section_title": section_title or "",
        "source": source,
        "source_type": SOURCE_TYPE_LITERAL,
        "metadata": metadata or {},
    }


def _extract_abilities(df: pd.DataFrame, source: str) -> list[dict[str, Any]]:
    """Level 스케일 행만 사용. content=Element Name, level=Data Value."""
    out: list[dict[str, Any]] = []
    cols = [c for c in df.columns if c]
    need = {"Title", "Element Name", "Scale ID", "Scale Name", "Data Value"}
    if not need.issubset(set(str(c) for c in cols)):
        return out
    for _, row in df.iterrows():
        scale_id = str(row.get("Scale ID", "")).strip().upper()
        if scale_id != "LV":  # Level only
            continue
        title = str(row.get("Title", "")).strip()
        elem = str(row.get("Element Name", "")).strip()
        if not elem:
            continue
        try:
            level_val = float(row.get("Data Value", 0))
        except (TypeError, ValueError):
            level_val = None
        meta = {}
        if "O*NET-SOC Code" in df.columns:
            meta["onet_soc_code"] = str(row.get("O*NET-SOC Code", "")).strip()
        if "Element ID" in df.columns:
            meta["element_id"] = str(row.get("Element ID", "")).strip()
        out.append(
            _row_to_anchor(
                content=elem,
                category="능력",
                section_title=title,
                source=source,
                level=int(level_val) if level_val is not None and 1 <= level_val <= 8 else None,
                metadata=meta,
            )
        )
    return out


def _extract_task_statements(df: pd.DataFrame, source: str) -> list[dict[str, Any]]:
    """한 행 = 한 문장(과제). content=Task."""
    out: list[dict[str, Any]] = []
    if "Task" not in df.columns or "Title" not in df.columns:
        return out
    for _, row in df.iterrows():
        task = str(row.get("Task", "")).strip()
        if not task:
            continue
        title = str(row.get("Title", "")).strip()
        meta = {}
        if "O*NET-SOC Code" in df.columns:
            meta["onet_soc_code"] = str(row.get("O*NET-SOC Code", "")).strip()
        if "Task ID" in df.columns:
            meta["task_id"] = row.get("Task ID")
        if "Task Type" in df.columns:
            meta["task_type"] = str(row.get("Task Type", "")).strip()
        out.append(
            _row_to_anchor(
                content=task,
                category="과제",
                section_title=title,
                source=source,
                level=None,
                metadata=meta,
            )
        )
    return out


def _extract_technology_skills(df: pd.DataFrame, source: str) -> list[dict[str, Any]]:
    """content=Example 또는 Commodity Title."""
    out: list[dict[str, Any]] = []
    has_ex = "Example" in df.columns
    has_title = "Commodity Title" in df.columns
    if not has_ex and not has_title:
        return out
    title_col = "Title" if "Title" in df.columns else None
    for _, row in df.iterrows():
        content = str(row.get("Example", "")).strip() if has_ex else str(row.get("Commodity Title", "")).strip()
        if not content:
            continue
        section_title = str(row.get(title_col, "")).strip() if title_col else ""
        meta = {}
        if "O*NET-SOC Code" in df.columns:
            meta["onet_soc_code"] = str(row.get("O*NET-SOC Code", "")).strip()
        if "Commodity Code" in df.columns:
            meta["commodity_code"] = row.get("Commodity Code")
        out.append(
            _row_to_anchor(
                content=content,
                category="기술",
                section_title=section_title,
                source=source,
                level=None,
                metadata=meta,
            )
        )
    return out


def _extract_work_styles(df: pd.DataFrame, source: str) -> list[dict[str, Any]]:
    """Work Styles Impact(WI) 스케일 행 사용. content=Element Name, level=Data Value 구간 매핑."""
    out: list[dict[str, Any]] = []
    need = {"Title", "Element Name", "Scale ID", "Data Value"}
    if not need.issubset(set(str(c) for c in df.columns)):
        return out
    for _, row in df.iterrows():
        scale_id = str(row.get("Scale ID", "")).strip().upper()
        if scale_id != "WI":  # Work Styles Impact
            continue
        title = str(row.get("Title", "")).strip()
        elem = str(row.get("Element Name", "")).strip()
        if not elem:
            continue
        try:
            val = float(row.get("Data Value", 0))
            level = max(1, min(8, int(round(val)))) if val is not None else None
        except (TypeError, ValueError):
            level = None
        meta = {}
        if "O*NET-SOC Code" in df.columns:
            meta["onet_soc_code"] = str(row.get("O*NET-SOC Code", "")).strip()
        if "Element ID" in df.columns:
            meta["element_id"] = str(row.get("Element ID", "")).strip()
        out.append(
            _row_to_anchor(
                content=elem,
                category="업무스타일",
                section_title=title,
                source=source,
                level=level,
                metadata=meta,
            )
        )
    return out


class OnetXlsxStrategy(ExcelExtractStrategy):
    """O*NET xlsx 4종을 파일명으로 구분해 통합 스키마 리스트로 반환."""

    def extract(self, xlsx_path: Path) -> list[dict[str, Any]]:
        path = Path(xlsx_path)
        if not path.suffix.lower() == ".xlsx":
            return []
        stem = path.stem.lower()
        source = path.name

        df = pd.read_excel(path, engine="openpyxl")
        if df is None or df.empty:
            return []

        if "abilities" in stem:
            return _extract_abilities(df, source)
        if "task statements" in stem:
            return _extract_task_statements(df, source)
        if "technology skills" in stem:
            return _extract_technology_skills(df, source)
        if "work styles" in stem:
            return _extract_work_styles(df, source)
        return []
