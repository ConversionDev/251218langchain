"""Soccer Spokes Services 모듈

- Rule 기반 엔티티 처리: PlayerService, ScheduleService, StadiumService, TeamService.
- 임베딩: embedding_service.run_embedding_sync_single_entity (LangGraph 노드에서 호출).
"""

from .embedding_service import run_embedding_sync_single_entity  # type: ignore
from .soccer_service import (  # type: ignore
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
    "run_embedding_sync_single_entity",
]
