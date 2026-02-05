"""
Soccer 임베딩 동기화 (백그라운드 태스크용).

버튼 클릭 시 BackgroundTasks에서 호출.
run_embedding_sync_task(job_id, entities) → LangGraph 오케스트레이터 → *_embeddings 저장.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_embeddings_model():
    """HuggingFaceEmbeddings 생성 (config 기반)."""
    from core.config import get_settings  # type: ignore

    settings = get_settings()
    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        device = getattr(settings, "embedding_device", None) or "cuda"
        model = HuggingFaceEmbeddings(
            model_name=settings.default_embedding_model,
            model_kwargs={"device": device},
        )
        model.embed_query("test")
        return model
    except Exception as e:
        logger.exception("임베딩 모델 로드 실패: %s", e)
        raise


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
        embeddings_model = _get_embeddings_model()
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
