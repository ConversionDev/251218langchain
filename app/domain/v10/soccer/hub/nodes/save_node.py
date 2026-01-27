"""DB 저장 노드

규칙 기반으로 변환된 데이터를 Neon DB에 저장합니다.
"""

import logging
from typing import Dict, Any

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore

logger = logging.getLogger(__name__)


def save_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    DB 저장 노드.

    규칙 기반으로 변환된 데이터를 Repository를 통해 Neon DB에 저장합니다.

    Args:
        state: Soccer 데이터 처리 상태

    Returns:
        업데이트된 상태 (saved_count 포함)
    """
    transformed_data = state.get("transformed_data", [])
    data_type = state.get("data_type", "unknown")
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")
    existing_errors = state.get("errors", [])
    errors = existing_errors.copy() if existing_errors else []

    logger.info(f"[SaveNode] {data_type} DB 저장 시작: {len(transformed_data)}개")

    saved_count = 0

    # DB 세션이 없으면 저장하지 않음
    if db is None:
        logger.warning(f"[SaveNode] {data_type} DB 세션이 없어 저장을 건너뜁니다.")
        new_path = processing_path + " -> Save(Skipped)"
        return {
            "saved_count": 0,
            "processing_path": new_path,
        }

    try:
        # 데이터 타입별 Repository 가져오기
        repository = _get_repository(data_type)

        if repository is None:
            logger.error(f"[SaveNode] {data_type}에 대한 Repository를 찾을 수 없습니다.")
            new_path = processing_path + " -> Save(Error)"
            return {
                "saved_count": 0,
                "processing_path": new_path,
            }

        # 각 데이터 저장
        for item in transformed_data:
            try:
                if repository.save(item, db):
                    saved_count += 1
            except Exception as e:
                errors.append({
                    "id": item.get("id"),
                    "error": f"DB 저장 실패: {str(e)}"
                })
                logger.warning(f"[SaveNode] {data_type} ID {item.get('id')} 저장 실패: {str(e)}")

        logger.info(f"[SaveNode] {data_type} DB 저장 완료: {saved_count}개 저장됨")

    except Exception as e:
        logger.error(f"[SaveNode] {data_type} DB 저장 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()

    new_path = processing_path + " -> Save"

    # 저장 실패 여부 확인 (재시도 로직을 위해)
    total_items = len(transformed_data)
    save_failed = saved_count == 0 and total_items > 0

    return {
        "saved_count": saved_count,
        "errors": errors,
        "save_failed": save_failed,
        "processing_path": new_path,
    }


def _get_repository(data_type: str):
    """데이터 타입에 맞는 Repository 인스턴스 반환"""
    try:
        if data_type == "players":
            from domain.v10.soccer.hub.repositories.player_repository import PlayerRepository  # type: ignore
            return PlayerRepository()
        elif data_type == "teams":
            from domain.v10.soccer.hub.repositories.team_repository import TeamRepository  # type: ignore
            return TeamRepository()
        elif data_type == "stadiums":
            from domain.v10.soccer.hub.repositories.stadium_repository import StadiumRepository  # type: ignore
            return StadiumRepository()
        elif data_type == "schedules":
            from domain.v10.soccer.hub.repositories.schedule_repository import ScheduleRepository  # type: ignore
            return ScheduleRepository()
        else:
            logger.error(f"[SaveNode] 알 수 없는 데이터 타입: {data_type}")
            return None
    except Exception as e:
        logger.error(f"[SaveNode] Repository 가져오기 실패: {str(e)}")
        return None
