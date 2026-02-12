"""
Excel 추출 소스 식별자.

O*NET competency_anchors xlsx 4종. 파일명/시트 타입에 따라 매핑 시 사용.
"""

from enum import Enum


class ExcelSourceType(str, Enum):
    """O*NET xlsx 유형. data/competency_anchors README §1과 대응."""

    ABILITIES = "Abilities"           # 능력(Element Name + Level)
    TASK_STATEMENTS = "Task Statements"  # 과제 문장(Task)
    TECHNOLOGY_SKILLS = "Technology Skills"  # 기술 예시
    WORK_STYLES = "Work Styles"       # 업무 스타일(Element Name + DR/WI)
