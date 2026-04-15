"""
Competency anchors raw → prepared: xlsx(ONET) + pdf(NCS) 전략 분기 후 JSONL.

- .xlsx: OnetXlsxStrategy → list[dict]
- .pdf: PDF 전략(Structural 등)으로 텍스트 추출 → 청크 단위로 list[dict], source_type=NCS
- 통합 후 unique_id 부여, limit 건수만 prepared/competency_rows.jsonl 로 저장.
"""

import json
from pathlib import Path
from typing import Any, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_competency_raw_dir() -> Path:
    """Competency raw 디렉터리. core.paths 기준."""
    from core.paths import get_data_dir  # type: ignore
    return get_data_dir() / "competency_anchors" / "raw"


def get_competency_prepared_dir() -> Path:
    """Competency prepared 디렉터리. core.paths 기준."""
    from core.paths import get_data_dir  # type: ignore
    return get_data_dir() / "competency_anchors" / "prepared"


def get_competency_sft_dir() -> Path:
    """Competency SFT 학습 데이터 디렉터리. data/competency_anchors/sft/."""
    from core.paths import get_data_dir  # type: ignore
    d = get_data_dir() / "competency_anchors" / "sft"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_unique_id(rows: List[dict[str, Any]], source: str, prefix: str = "") -> None:
    """row에 unique_id 없으면 source + prefix + 인덱스로 채움."""
    for i, r in enumerate(rows):
        if r.get("unique_id"):
            continue
        r["unique_id"] = f"{source}_{prefix}{i}"


def _extract_xlsx(path: Path) -> List[dict[str, Any]]:
    """xlsx → OnetXlsxStrategy로 통합 스키마 list[dict] 반환."""
    from domain.shared.strategy_imples.onet_xlsx import OnetXlsxStrategy  # type: ignore
    strategy = OnetXlsxStrategy()
    return strategy.extract(path)


def _extract_pdf(path: Path, chunk_size: int = 600, chunk_overlap: int = 80) -> List[dict[str, Any]]:
    """PDF → 텍스트 추출 후 청킹하여 NCS 스타일 list[dict] 반환."""
    from domain.shared.strategies.pdf_strategy import StrategyFactory  # type: ignore
    strategy = StrategyFactory.get_strategy(path)
    text = strategy.extract(path)
    if not text or not text.strip():
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_text(text.strip())
    source = path.stem
    rows: List[dict[str, Any]] = []
    for i, content in enumerate(chunks):
        if not content.strip():
            continue
        rows.append({
            "content": content.strip(),
            "category": "지식",
            "level": None,
            "section_title": "",
            "source": source,
            "source_type": "NCS",
            "metadata": {"pdf_page_chunk": i},
            "unique_id": f"{source}_ncs_{i}",
        })
    return rows


def extract_raw_to_prepared(
    raw_dir: Optional[Path] = None,
    prepared_dir: Optional[Path] = None,
    limit: Optional[int] = None,
) -> List[dict[str, Any]]:
    """
    raw 내 .xlsx, .pdf를 전략별로 추출 후 통합하고, prepared/competency_rows.jsonl 로 저장.
    limit 이 None 이면 전체, 정수면 해당 건수만 저장.

    Returns:
        저장된 행 목록.
    """
    raw = raw_dir or get_competency_raw_dir()
    prepared = prepared_dir or get_competency_prepared_dir()
    if not raw.exists():
        return []

    prepared.mkdir(parents=True, exist_ok=True)
    out_path = prepared / "competency_rows.jsonl"

    all_rows: List[dict[str, Any]] = []

    for path in sorted(raw.iterdir()):
        if path.suffix.lower() == ".xlsx":
            try:
                rows = _extract_xlsx(path)
                _ensure_unique_id(rows, path.stem, "onet_")
                all_rows.extend(rows)
            except Exception as e:
                raise RuntimeError(f"xlsx 추출 실패: {path} — {e}") from e
        elif path.suffix.lower() == ".pdf":
            try:
                rows = _extract_pdf(path)
                all_rows.extend(rows)
            except Exception as e:
                raise RuntimeError(f"pdf 추출 실패: {path} — {e}") from e

    if not all_rows:
        out_path.write_text("", encoding="utf-8")
        return []

    to_save = all_rows[:limit] if limit is not None else all_rows
    with out_path.open("w", encoding="utf-8") as f:
        for row in to_save:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return to_save
