"""검증·에러 처리 (processing)

validate_node: 데이터 검증 (필수 필드, 타입).
error_handler_node: 검증 에러 수집·로깅 후 흐름 계속.
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
