"""최종 처리 노드

휴리스틱 처리를 완료하고 결과를 정리합니다.
"""

import logging
from typing import Dict, Any

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore

logger = logging.getLogger(__name__)


def finalize_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    최종 처리 노드.
    
    검증, 변환, 저장된 데이터를 정리하여 최종 결과를 생성합니다.
    규칙 기반으로 Neon DB에 저장된 결과를 반환합니다.
    
    Args:
        state: Soccer 데이터 처리 상태
        
    Returns:
        업데이트된 상태 (result 포함)
    """
    transformed_data = state.get("transformed_data", [])
    saved_count = state.get("saved_count", 0)
    errors = state.get("errors", [])
    data_type = state.get("data_type", "unknown")
    processing_path = state.get("processing_path", "Start")
    
    logger.info(f"[FinalizeNode] {data_type} 최종 처리 시작: {len(transformed_data)}개, 저장됨: {saved_count}개")
    
    # 최종 결과 생성
    result = {
        "processed": saved_count,  # 실제 저장된 개수
        "db": saved_count,  # 규칙 기반으로 Neon DB에 저장된 개수
        "vector": 0,  # 벡터 DB 저장 없음 (휴리스틱 처리)
        "total": len(state.get("data", [])),
        "errors": errors,
    }
    
    logger.info(f"[FinalizeNode] {data_type} 최종 처리 완료: {result}")
    
    new_path = processing_path + " -> Finalize"
    
    return {
        "result": result,
        "processing_path": new_path,
    }
