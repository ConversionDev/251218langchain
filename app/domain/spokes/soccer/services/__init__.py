"""Soccer Spokes Services 모듈

- Rule 기반 엔티티 처리: PlayerService, ScheduleService, StadiumService, TeamService.
- 임베딩: 코드 생성 + 동기화 (embedding_service).
"""

from .embedding_service import (  # type: ignore
    generate_and_write_embedding_module,
    generate_and_write_soccer_embeddings,
    generate_embedding_module_code,
    run_embedding_sync,
)
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
    "generate_and_write_embedding_module",
    "generate_and_write_soccer_embeddings",
    "generate_embedding_module_code",
    "run_embedding_sync",
]
