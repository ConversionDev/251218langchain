"""
Soccer 임베딩 동기화 워커.

Redis 큐(soccer:embedding:jobs)에서 job을 꺼내 run_embedding_sync_orchestrate(LangGraph) 호출.

실행 (app 디렉터리에서):
    cd app
    python -m api.shared.embedding_worker
"""

import logging
import sys
import time
from pathlib import Path

# 프로젝트 루트에서 실행한 경우 app을 path에 추가
_APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 2.0


def _get_embeddings_model():
    """FastAPI 서버와 동일한 방식으로 HuggingFaceEmbeddings 생성."""
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


def _run_job(payload: dict) -> None:
    job_id = payload.get("job_id") or "unknown"
    entities = payload.get("entities")

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
        logger.info("[embedding_worker] job_id=%s 완료 results=%s", job_id, result.get("results"))
    except Exception as e:
        logger.exception("[embedding_worker] job_id=%s 실패: %s", job_id, e)
        set_embedding_job_status(
            job_id,
            "failed",
            result={"error": str(e)},
        )
    finally:
        db.close()


def main() -> None:
    from api.shared.redis import get_redis, pop_embedding_job  # type: ignore

    if get_redis() is None:
        logger.error("Redis 연결 불가. UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN 확인.")
        sys.exit(1)

    logger.info("임베딩 워커 시작 (폴링 간격 %.1fs)", POLL_INTERVAL_SEC)
    while True:
        try:
            payload = pop_embedding_job()
            if payload:
                _run_job(payload)
            else:
                time.sleep(POLL_INTERVAL_SEC)
        except KeyboardInterrupt:
            logger.info("워커 종료")
            break
        except Exception as e:
            logger.exception("폴링 중 오류: %s", e)
            time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
