"""
Hub 공통 서비스

전역(여러 도메인)에서 사용하는 서비스.
Soccer Rule 서비스는 domain.spokes.soccer.services 에서 re-export.
"""

from domain.spokes.soccer.services import (  # type: ignore
    PlayerService,
    ScheduleService,
    StadiumService,
    TeamService,
)

__all__ = [
    "PlayerService",
    "ScheduleService",
    "StadiumService",
    "TeamService",
]
