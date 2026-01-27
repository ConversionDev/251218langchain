"""데이터 검증 노드

휴리스틱 규칙에 따라 데이터를 검증합니다.
"""

import logging
from typing import Dict, Any

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore

logger = logging.getLogger(__name__)


def validate_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    데이터 검증 노드.
    
    휴리스틱 규칙에 따라 필수 필드와 데이터 타입을 검증합니다.
    
    Args:
        state: Soccer 데이터 처리 상태
        
    Returns:
        업데이트된 상태 (validated_data, errors 포함)
    """
    data = state.get("data", [])
    data_type = state.get("data_type", "unknown")
    processing_path = state.get("processing_path", "Start")
    
    logger.info(f"[ValidateNode] {data_type} 데이터 검증 시작: {len(data)}개")
    
    validated_data = []
    errors = []
    
    # 데이터 타입별 필수 필드 정의
    required_fields_map = {
        "players": ["id", "player_name", "team_id"],
        "teams": ["id", "team_code", "team_name"],
        "stadiums": ["id", "stadium_code", "statdium_name"],
        "schedules": ["id", "stadium_id", "hometeam_id", "awayteam_id", "stadium_code", "sche_date", "gubun", "hometeam_code", "awayteam_code"],
    }
    
    required_fields = required_fields_map.get(data_type, ["id"])
    
    for item in data:
        try:
            # 필수 필드 검증
            missing_fields = []
            for field in required_fields:
                if field not in item or item[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                errors.append({
                    "id": item.get("id"),
                    "error": f"필수 필드 누락: {', '.join(missing_fields)}"
                })
                logger.warning(f"[ValidateNode] {data_type} ID {item.get('id')}: 필수 필드 누락")
                continue
            
            # 기본 데이터 타입 검증
            if not isinstance(item.get("id"), (int, str)):
                errors.append({
                    "id": item.get("id"),
                    "error": "id는 int 또는 str이어야 합니다"
                })
                logger.warning(f"[ValidateNode] {data_type} ID {item.get('id')}: id 타입 오류")
                continue
            
            # 검증 통과
            validated_data.append(item)
            
        except Exception as e:
            errors.append({
                "id": item.get("id"),
                "error": f"검증 중 오류: {str(e)}"
            })
            logger.error(f"[ValidateNode] {data_type} ID {item.get('id')} 검증 실패: {str(e)}")
    
    logger.info(f"[ValidateNode] {data_type} 검증 완료: {len(validated_data)}개 통과, {len(errors)}개 실패")
    
    new_path = processing_path + " -> Validate"
    
    return {
        "validated_data": validated_data,
        "errors": errors,
        "processing_path": new_path,
    }
