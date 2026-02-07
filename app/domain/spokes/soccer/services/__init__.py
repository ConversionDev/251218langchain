"""Soccer Spokes Services 모듈

- Rule 기반 엔티티 처리: PlayerService, ScheduleService, StadiumService, TeamService.
- 임베딩: embedding_service.fill_embeddings_for_entity / run_embedding_sync_single_entity (단일 테이블 베이스 컬럼 채움).
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
