"""
Player 데이터 처리 State 정의
"""

from typing import Any, Dict, List, Optional

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore


class PlayerProcessingState(BaseProcessingState, total=False):
    """Player 데이터 처리 워크플로우 상태 정의."""

    # Player 특화 필드 (필요시 추가)
    # 예: player_specific_field: Optional[str]
