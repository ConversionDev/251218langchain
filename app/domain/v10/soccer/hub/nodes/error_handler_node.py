"""에러 처리 노드

검증 단계에서 발생한 에러를 수집하고 로깅합니다.
에러가 있어도 처리 흐름을 계속 진행합니다.
"""

import logging
from typing import Dict, Any

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore

logger = logging.getLogger(__name__)


def error_handler_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    에러 처리 노드.
    
    검증 단계에서 발생한 에러를 수집하고 로깅합니다.
    에러가 있어도 처리 흐름을 계속 진행합니다 (에러가 있는 데이터는 건너뛰고 계속 진행).
    
    Args:
        state: Soccer 데이터 처리 상태
        
    Returns:
        업데이트된 상태 (에러 정보 포함)
    """
    errors = state.get("errors", [])
    data_type = state.get("data_type", "unknown")
    processing_path = state.get("processing_path", "Start")
    validated_data = state.get("validated_data", [])
    
    logger.info(f"[ErrorHandlerNode] {data_type} 에러 처리 시작: {len(errors)}개 에러")
    
    # 에러가 있으면 로깅
    if errors:
        logger.warning(f"[ErrorHandlerNode] {data_type} 검증 중 {len(errors)}개 에러 발생:")
        for error in errors[:10]:  # 최대 10개만 로깅
            logger.warning(f"  - ID {error.get('id')}: {error.get('error')}")
        if len(errors) > 10:
            logger.warning(f"  ... 외 {len(errors) - 10}개 에러")
    
    # 에러가 있어도 처리 계속 진행 (에러가 있는 데이터는 이미 validated_data에서 제외됨)
    logger.info(f"[ErrorHandlerNode] {data_type} 에러 처리 완료: {len(validated_data)}개 데이터 계속 처리")
    
    new_path = processing_path + " -> ErrorHandler"
    
    return {
        "processing_path": new_path,
        # errors는 그대로 유지 (이미 validated_data에서 제외됨)
    }
