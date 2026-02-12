"""
PDF 추출 전략 — GoF Strategy 패턴.

- 추상 클래스: PDFExtractStrategy (extract(pdf_path) -> str).
- StrategyFactory: 파일명/경로 키워드로 전략 선택 (pdf_strategy.md §3 Step 1 Primary).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from domain.shared.strategies.pdf_enums import PdfStrategyType  # type: ignore

# disclosure 파이프라인과 동일한 페이지 구분자 (pdf_extract, pdf_ingest 호환)
PAGE_SEP = "\n--- Page Break ---\n"


class PDFExtractStrategy(ABC):
    """PDF에서 텍스트를 추출하는 전략의 추상 인터페이스."""

    @abstractmethod
    def extract(self, pdf_path: Path) -> str:
        """
        PDF 전체 텍스트를 UTF-8 문자열로 반환.
        공시(disclosures) 호환을 위해 페이지 경계는 PAGE_SEP로 구분하는 것을 권장.
        """
        ...


class StrategyFactory:
    """파일명/경로 키워드로 전략 선택. pdf_strategy.md §3 Step 1 Primary 기준."""

    # 키워드(소문자) → 전략 타입. 경로 또는 파일명에 포함되면 해당 전략 선택.
    _KEYWORD_STRATEGY: list[tuple[list[str], PdfStrategyType]] = [
        (["ncs", "역량", "수행준거"], PdfStrategyType.Structural),
        (["ifrs", "iso", "oecd", "공시"], PdfStrategyType.FastExtract),
        (["esg", "지속가능", "sustainability"], PdfStrategyType.Intelligent),
    ]

    @classmethod
    def get_strategy(cls, path: Union[Path, str]) -> PDFExtractStrategy:
        """
        경로/파일명 키워드로 전략 인스턴스 반환.
        매칭 없으면 FastExtract(기본) 반환.
        """
        path_str = (path if isinstance(path, str) else str(path)).lower()
        for keywords, strategy_type in cls._KEYWORD_STRATEGY:
            if any(kw in path_str for kw in keywords):
                return cls.get_strategy_by_type(strategy_type)
        return cls.get_strategy_by_type(PdfStrategyType.FastExtract)

    @classmethod
    def get_strategy_by_type(cls, strategy_type: PdfStrategyType) -> PDFExtractStrategy:
        """전략 번호(0~2)로 구현체 반환. Secondary 라우팅·캐시 결과에 사용."""
        if strategy_type == PdfStrategyType.FastExtract:
            from domain.shared.strategy_imples.py_mu_pdf import PyMuPdfStrategy  # type: ignore
            return PyMuPdfStrategy()
        if strategy_type == PdfStrategyType.Structural:
            from domain.shared.strategy_imples.pdf_plumber import PdfPlumberStrategy  # type: ignore
            return PdfPlumberStrategy()
        if strategy_type == PdfStrategyType.Intelligent:
            # LlamaParse 구현 전까지 FastExtract로 fallback
            from domain.shared.strategy_imples.py_mu_pdf import PyMuPdfStrategy  # type: ignore
            return PyMuPdfStrategy()
        from domain.shared.strategy_imples.py_mu_pdf import PyMuPdfStrategy  # type: ignore
        return PyMuPdfStrategy()
