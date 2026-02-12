"""
FastExtract 전략 — PyMuPDF(fitz).

공시(disclosures) 대량 텍스트화에 최적. pdf_strategy.md §2 FastExtract.
의존성: pymupdf==1.25.1 (requirements.txt).
"""

from pathlib import Path

from domain.shared.strategies.pdf_strategy import PAGE_SEP, PDFExtractStrategy  # type: ignore


class PyMuPdfStrategy(PDFExtractStrategy):
    """PyMuPDF를 사용한 고속 텍스트 추출. 페이지별로 PAGE_SEP로 연결."""

    def extract(self, pdf_path: Path) -> str:
        import fitz  # type: ignore[import-untyped]

        doc = fitz.open(pdf_path)
        try:
            parts = [page.get_text() for page in doc]
            return PAGE_SEP.join(parts)
        finally:
            doc.close()
