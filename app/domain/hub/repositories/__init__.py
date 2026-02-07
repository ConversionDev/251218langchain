"""
Hub Repositories — 통합 Repository 모듈

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from .disclosure_repository import (  # type: ignore
    fill_embeddings_for_disclosures,
    get_disclosure_doc_count,
    save_batch as disclosure_save_batch,
    search_disclosures,
)
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
    "disclosure_save_batch",
    "fill_embeddings_for_disclosures",
    "get_disclosure_doc_count",
    "search_disclosures",
]
