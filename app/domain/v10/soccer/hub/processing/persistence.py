"""저장·재시도·최종 처리 (processing)

save_node: DB 저장.
retry_save_node: 저장 실패 시 재시도.
finalize_node: 최종 결과 정리.
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

    if db is None:
        logger.warning(f"[SaveNode] {data_type} DB 세션이 없어 저장을 건너뜁니다.")
        return {
            "saved_count": 0,
            "processing_path": processing_path + " -> Save(Skipped)",
        }

    try:
        # 데이터 타입별 Repository 가져오기
        repository = _get_repository(data_type)

        if repository is None:
            logger.error(f"[SaveNode] {data_type}에 대한 Repository를 찾을 수 없습니다.")
            return {
                "saved_count": 0,
                "processing_path": processing_path + " -> Save(Error)",
            }

        sorted_data = sorted(
            transformed_data,
            key=lambda x: x.get("id", 0) if x.get("id") is not None else 0
        )

        if hasattr(repository, "save_batch"):
            saved_count = repository.save_batch(sorted_data, db)
        else:
            for item in sorted_data:
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

    return {
        "saved_count": saved_count,
        "errors": errors,
        "save_failed": saved_count == 0 and len(transformed_data) > 0,
        "processing_path": processing_path + " -> Save",
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


def finalize_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    최종 처리. 검증·저장 결과를 정리하여 result를 생성합니다.
    """
    transformed_data = state.get("transformed_data", [])
    saved_count = state.get("saved_count", 0)
    errors = state.get("errors", [])
    data_type = state.get("data_type", "unknown")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[FinalizeNode] {data_type} 최종 처리 시작: {len(transformed_data)}개, 저장됨: {saved_count}개")

    result = {
        "processed": saved_count,
        "db": saved_count,
        "vector": 0,
        "total": len(state.get("data", [])),
        "errors": errors,
    }

    logger.info(f"[FinalizeNode] {data_type} 최종 처리 완료: {result}")

    new_path = processing_path + " -> Finalize"

    return {
        "result": result,
        "processing_path": new_path,
    }
