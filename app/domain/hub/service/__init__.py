"""
Hub 공통 서비스

전역(여러 도메인)에서 사용하는 서비스.
Soccer Rule 서비스는 domain.spokes.soccer.services 에서 re-export.
"""

from .semantic_classifier import classify, is_classifier_available
from domain.spokes.soccer.services import (  # type: ignore
    PlayerService,
    ScheduleService,
    StadiumService,
    TeamService,
)

__all__ = [
    "classify",
    "is_classifier_available",
    "PlayerService",
    "ScheduleService",
    "StadiumService",
    "TeamService",
]
