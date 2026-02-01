"""Soccer Spokes Services 모듈

- Rule 기반 엔티티 처리: PlayerService, ScheduleService, StadiumService, TeamService.
- 코드 생성: ExaOne으로 soccer_embeddings.py 생성 (embedding_generator_service).
"""

from .embedding_generator_service import (  # type: ignore
    generate_and_write_embedding_module,
    generate_and_write_soccer_embeddings,
    generate_embedding_module_code,
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
]
