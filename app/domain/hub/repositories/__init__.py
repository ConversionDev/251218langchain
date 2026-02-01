"""
Hub Repositories — 통합 Repository 모듈

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from .soccer_repository import (  # type: ignore
    PlayerRepository,
    ScheduleRepository,
    StadiumRepository,
    TeamRepository,
)

__all__ = [
    "PlayerRepository",
    "ScheduleRepository",
    "StadiumRepository",
    "TeamRepository",
]
