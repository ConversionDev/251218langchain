"""
Disclosure raw PDF → prepared txt 변환.

- raw/*.pdf 를 domain PDF 전략(PyMuPDF 등)으로 텍스트 추출.
- prepared/*.txt 로 저장 (페이지 구분자 PAGE_SEP).
"""

from pathlib import Path
from typing import List, Optional, Tuple

from domain.shared.strategies.pdf_strategy import StrategyFactory  # type: ignore


def get_disclosure_raw_dir() -> Path:
    """Disclosure raw PDF 디렉터리. core.paths 기준."""
    from core.paths import get_data_dir  # type: ignore
    return get_data_dir() / "disclosure" / "raw"


def get_disclosure_prepared_dir() -> Path:
    """Disclosure prepared txt 디렉터리. core.paths 기준."""
    from core.paths import get_data_dir  # type: ignore
    return get_data_dir() / "disclosure" / "prepared"


def extract_raw_to_prepared(
    raw_dir: Optional[Path] = None,
    prepared_dir: Optional[Path] = None,
) -> List[Tuple[Path, Path]]:
    """
    raw 내 모든 .pdf를 텍스트로 추출해 prepared에 .txt로 저장.

    Returns:
        성공한 (pdf_path, txt_path) 목록.
    """
    raw = raw_dir or get_disclosure_raw_dir()
    prepared = prepared_dir or get_disclosure_prepared_dir()
    if not raw.exists():
        return []
    prepared.mkdir(parents=True, exist_ok=True)

    result: List[Tuple[Path, Path]] = []
    for pdf_path in sorted(raw.glob("*.pdf")):
        try:
            strategy = StrategyFactory.get_strategy(pdf_path)
            text = strategy.extract(pdf_path)
            txt_path = prepared / f"{pdf_path.stem}.txt"
            txt_path.write_text(text, encoding="utf-8")
            result.append((pdf_path, txt_path))
        except Exception as e:
            raise RuntimeError(f"PDF 텍스트 추출 실패: {pdf_path} — {e}") from e
    return result
