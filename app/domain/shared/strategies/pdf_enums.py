"""
PDF 추출 전략 식별자.

pdf_strategy.md 전략 매트릭스와 1:1 대응.
Secondary 라우팅(ExaOne 샘플 분석) 시 전략 번호(0~2)로 할당·캐시할 때 사용.
"""

from enum import IntEnum


class PdfStrategyType(IntEnum):
    """전략 번호(0~2) 및 전략명. md §3 Step 1 Secondary 참조."""

    FastExtract = 0   # PyMuPDF — disclosures (IFRS, ISO, OECD)
    Structural = 1    # pdfplumber — competency_anchors (NCS)
    Intelligent = 2   # LlamaParse — ESG/지속가능경영보고서 등
