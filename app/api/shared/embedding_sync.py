"""
Soccer 임베딩 동기화 (백그라운드 태스크용).

버튼 클릭 시 BackgroundTasks에서 호출.
run_embedding_sync_task(job_id, entities) → LangGraph 오케스트레이터 → 베이스 테이블(players 등)의 embedding 컬럼 채움.
FlagEmbedding BGE-m3 사용 (domain.shared.embedding). 단일 테이블 가이드.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def run_embedding_sync_task(job_id: str, entities: Optional[List[str]] = None) -> None:
    """
    임베딩 동기화 실행. Redis 상태를 completed/failed로 갱신.
    BackgroundTasks에서 호출.
    """
    from api.shared.redis import set_embedding_job_status  # type: ignore
    from core.database import SessionLocal  # type: ignore
    from domain.hub.orchestrators.soccer_orchestrator import run_embedding_sync_orchestrate  # type: ignore

    set_embedding_job_status(job_id, "processing")

    db = SessionLocal()
    try:
        from domain.shared.embedding import get_embedding_model  # type: ignore

        embeddings_model = get_embedding_model(use_fp16=True)
        result = run_embedding_sync_orchestrate(db, embeddings_model, entities=entities)
        set_embedding_job_status(
            job_id,
            "completed",
            result=result.get("results"),
        )
        logger.info("[embedding_sync] job_id=%s 완료 results=%s", job_id, result.get("results"))
    except Exception as e:
        logger.exception("[embedding_sync] job_id=%s 실패: %s", job_id, e)
        set_embedding_job_status(
            job_id,
            "failed",
            result={"error": str(e)},
        )
    finally:
        db.close()
