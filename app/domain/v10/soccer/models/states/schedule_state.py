"""
Schedule 데이터 처리 State 정의
"""

from typing import Any, Dict, List, Optional

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore


class ScheduleProcessingState(BaseProcessingState, total=False):
    """Schedule 데이터 처리 워크플로우 상태 정의."""

    # Schedule 특화 필드 (필요시 추가)
    # 예: schedule_specific_field: Optional[str]
