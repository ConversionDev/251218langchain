"""
임베딩 동기화 (백그라운드 태스크용).

범용 job_id·상태 등록. 도메인별 동기화는 호출측에서 구현.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def run_embedding_sync_task(job_id: str, entities: Optional[List[str]] = None) -> None:
    """
    임베딩 동기화 실행. Redis 상태를 completed로 갱신.
    (soccer 도메인 제거로 실제 동기화 로직 없음; 호환용 스텁.)
    """
    from api.shared.redis import set_embedding_job_status  # type: ignore

    set_embedding_job_status(job_id, "completed", result={"results": {}})
    logger.info("[embedding_sync] job_id=%s 스텁 완료 (동기화 없음)", job_id)
