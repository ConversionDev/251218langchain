"""
Hub Repositories — 통합 Repository 모듈

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from .competency_anchor_repository import (  # type: ignore
    fill_embeddings_for_anchors,
    get_anchor_doc_count,
    save_batch_upsert as competency_anchor_save_batch_upsert,
    search_competency_anchors_with_filter,
)
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
    "competency_anchor_save_batch_upsert",
    "disclosure_save_batch",
    "fill_embeddings_for_anchors",
    "fill_embeddings_for_disclosures",
    "get_anchor_doc_count",
    "get_disclosure_doc_count",
    "search_competency_anchors_with_filter",
    "search_disclosures",
]
