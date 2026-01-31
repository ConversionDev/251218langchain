"""v10 soccer spokes services

- 엔티티 처리: Rule 기반으로 Hub Repository를 사용해 관계형 DB에 저장.
- 코드 생성: ExaOne으로 임베딩 모듈(*_embeddings.py) 생성.
"""

from domain.v10.soccer.spokes.services.embedding_generator_service import (  # type: ignore
    generate_and_write_embedding_module,
    generate_embedding_module_code,
)
from domain.v10.soccer.spokes.services.player_service import PlayerService  # type: ignore
from domain.v10.soccer.spokes.services.schedule_service import ScheduleService  # type: ignore
from domain.v10.soccer.spokes.services.stadium_service import StadiumService  # type: ignore
from domain.v10.soccer.spokes.services.team_service import TeamService  # type: ignore

__all__ = [
    "PlayerService",
    "ScheduleService",
    "StadiumService",
    "TeamService",
    "generate_embedding_module_code",
    "generate_and_write_embedding_module",
]
