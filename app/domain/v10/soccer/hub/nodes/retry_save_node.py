"""저장 재시도 노드

저장 실패 시 재시도 로직을 처리합니다.
최대 재시도 횟수 내에서 save 노드로 다시 이동합니다.
"""

import logging
from typing import Dict, Any

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore

logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 3


def retry_save_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    저장 재시도 노드.

    저장 실패 시 재시도 횟수를 증가시키고 save 노드로 다시 이동합니다.
    최대 재시도 횟수를 초과하면 finalize로 이동합니다.

    Args:
        state: Soccer 데이터 처리 상태

    Returns:
        업데이트된 상태 (재시도 횟수 증가)
    """
    save_retry_count = state.get("save_retry_count", 0)
    data_type = state.get("data_type", "unknown")
    processing_path = state.get("processing_path", "Start")

    new_retry_count = save_retry_count + 1

    logger.info(f"[RetrySaveNode] {data_type} 저장 재시도: {new_retry_count}/{MAX_RETRY_COUNT}회")

    if new_retry_count >= MAX_RETRY_COUNT:
        logger.warning(f"[RetrySaveNode] {data_type} 최대 재시도 횟수({MAX_RETRY_COUNT}회) 초과. 재시도 중단.")
        new_path = processing_path + " -> RetrySave(MaxReached)"
        return {
            "save_retry_count": new_retry_count,
            "save_failed": True,
            "processing_path": new_path,
        }

    new_path = processing_path + " -> RetrySave"

    return {
        "save_retry_count": new_retry_count,
        "save_failed": False,  # 재시도 가능
        "processing_path": new_path,
    }
