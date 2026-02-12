"""
Structural 전략 — pdfplumber.

표(Table) 구조 보존. competency_anchors(NCS) 수행준거 추출용. pdf_strategy.md §2 Structural.
의존성: pdfplumber (requirements.txt에 추가 필요).
"""

from pathlib import Path

from domain.shared.strategies.pdf_strategy import PAGE_SEP, PDFExtractStrategy  # type: ignore


class PdfPlumberStrategy(PDFExtractStrategy):
    """pdfplumber로 페이지·표 인식 후 텍스트 추출. 표는 행 단위로 이어 붙여 구조 보존."""

    def extract(self, pdf_path: Path) -> str:
        import pdfplumber  # type: ignore[import-untyped]

        parts: list[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # 표가 있으면 표 먼저 추출(구조 보존), 없으면 일반 텍스트
                tables = page.extract_tables()
                if tables:
                    page_parts = []
                    for table in tables:
                        for row in table:
                            if row and any(cell for cell in row):
                                line = "\t".join(str(cell or "").strip() for cell in row)
                                page_parts.append(line)
                        if page_parts:
                            page_parts.append("")
                    text = page.extract_text() or ""
                    if text.strip():
                        page_parts.append(text.strip())
                    parts.append("\n".join(page_parts).strip())
                else:
                    text = page.extract_text() or ""
                    parts.append(text.strip())
        return PAGE_SEP.join(parts)
