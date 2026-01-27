"""
Stadium 데이터 처리 State 정의
"""

from typing import Any, Dict, List, Optional

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore


class StadiumProcessingState(BaseProcessingState, total=False):
    """Stadium 데이터 처리 워크플로우 상태 정의."""

    # Stadium 특화 필드 (필요시 추가)
    # 예: stadium_specific_field: Optional[str]
