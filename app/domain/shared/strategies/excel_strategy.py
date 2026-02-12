"""
Excel 추출 전략 — GoF Strategy 패턴 (PDF와 동일 계층).

- 추상 클래스: ExcelExtractStrategy (extract(xlsx_path) -> list[dict]).
- 반환 dict는 competency_anchors 통합 스키마: content, category, level, section_title, source, source_type, metadata.
- ExcelStrategyFactory: 파일명으로 O*NET 시트 타입 추론 후 구현체 반환.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from domain.shared.strategies.excel_enums import ExcelSourceType  # type: ignore

# competency_anchors 통합 스키마 키 (README §2와 동일)
ANCHOR_KEYS = ("content", "category", "level", "section_title", "source", "source_type", "metadata")


class ExcelExtractStrategy(ABC):
    """xlsx에서 역량 anchor 행들을 추출하는 전략의 추상 인터페이스."""

    @abstractmethod
    def extract(self, xlsx_path: Path) -> list[dict[str, Any]]:
        """
        xlsx 전체를 읽어 통합 스키마 dict 리스트로 반환.
        각 dict는 content, category, level, section_title, source, source_type, metadata 포함.
        """
        ...


class ExcelStrategyFactory:
    """파일명으로 O*NET 시트 타입 추론 후 전략 반환."""

    _NAME_TO_TYPE: dict[str, ExcelSourceType] = {
        "abilities": ExcelSourceType.ABILITIES,
        "task statements": ExcelSourceType.TASK_STATEMENTS,
        "technology skills": ExcelSourceType.TECHNOLOGY_SKILLS,
        "work styles": ExcelSourceType.WORK_STYLES,
    }

    @classmethod
    def get_strategy(cls, path: Path | str) -> ExcelExtractStrategy:
        """xlsx 경로에 맞는 구현체 반환. O*NET 4종 파일명 지원."""
        from domain.shared.strategy_imples.onet_xlsx import OnetXlsxStrategy  # type: ignore
        return OnetXlsxStrategy()

    @classmethod
    def source_type_from_path(cls, path: Path | str) -> ExcelSourceType | None:
        """파일명에서 ExcelSourceType 추론. 매칭 없으면 None."""
        stem = Path(path).stem.lower()
        for key, st in cls._NAME_TO_TYPE.items():
            if key in stem:
                return st
        return None
