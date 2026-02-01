"""
Hub 공통 서비스

전역(여러 도메인)에서 사용하는 서비스.
Soccer Rule/임베딩 서비스는 domain.spokes.soccer.services 에서 re-export.
"""

from .semantic_classifier import classify, is_classifier_available
from domain.spokes.soccer.services import (  # type: ignore
    PlayerService,
    ScheduleService,
    StadiumService,
    TeamService,
    generate_and_write_embedding_module,
    generate_and_write_soccer_embeddings,
    generate_embedding_module_code,
)

__all__ = [
    "classify",
    "is_classifier_available",
    "PlayerService",
    "ScheduleService",
    "StadiumService",
    "TeamService",
    "generate_and_write_embedding_module",
    "generate_and_write_soccer_embeddings",
    "generate_embedding_module_code",
]
