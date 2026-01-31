"""데이터 변환 노드

휴리스틱 규칙에 따라 데이터를 변환합니다.
"""

import logging
from typing import Dict, Any

from domain.v10.soccer.models.states.base_state import BaseProcessingState  # type: ignore

logger = logging.getLogger(__name__)


def transform_node(state: BaseProcessingState) -> Dict[str, Any]:
    """
    데이터 변환 노드.
    
    휴리스틱 규칙에 따라 데이터 타입을 변환하고 기본값을 설정합니다.
    
    Args:
        state: Soccer 데이터 처리 상태
        
    Returns:
        업데이트된 상태 (transformed_data 포함)
    """
    validated_data = state.get("validated_data", [])
    data_type = state.get("data_type", "unknown")
    processing_path = state.get("processing_path", "Start")
    
    logger.info(f"[TransformNode] {data_type} 데이터 변환 시작: {len(validated_data)}개")
    
    transformed_data = []
    
    for item in validated_data:
        try:
            transformed_item = {}
            
            # 공통 필드 변환
            if "id" in item:
                transformed_item["id"] = int(item["id"]) if item["id"] is not None else None
            
            # 데이터 타입별 변환
            if data_type == "players":
                transformed_item.update(_transform_player(item))
            elif data_type == "teams":
                transformed_item.update(_transform_team(item))
            elif data_type == "stadiums":
                transformed_item.update(_transform_stadium(item))
            elif data_type == "schedules":
                transformed_item.update(_transform_schedule(item))
            else:
                # 기본 변환: 모든 필드를 그대로 유지
                transformed_item = item.copy()
            
            transformed_data.append(transformed_item)
            
        except Exception as e:
            logger.error(f"[TransformNode] {data_type} ID {item.get('id')} 변환 실패: {str(e)}")
            # 변환 실패 시 원본 유지
            transformed_data.append(item)
    
    logger.info(f"[TransformNode] {data_type} 변환 완료: {len(transformed_data)}개")
    
    new_path = processing_path + " -> Transform"
    
    return {
        "transformed_data": transformed_data,
        "processing_path": new_path,
    }


def _transform_player(item: Dict[str, Any]) -> Dict[str, Any]:
    """선수 데이터 변환"""
    return {
        "id": int(item["id"]),
        "player_name": str(item.get("player_name", "")).strip(),
        "team_id": int(item["team_id"]) if item.get("team_id") else None,
        "e_player_name": str(item.get("e_player_name", "")).strip() if item.get("e_player_name") else None,
        "nickname": str(item.get("nickname", "")).strip() if item.get("nickname") else None,
        "join_yyyy": int(item["join_yyyy"]) if item.get("join_yyyy") else None,
        "position": str(item.get("position", "")).strip() if item.get("position") else None,
        "back_no": int(item["back_no"]) if item.get("back_no") else None,
        "nation": str(item.get("nation", "")).strip() if item.get("nation") else None,
        "birth_date": str(item.get("birth_date", "")).strip() if item.get("birth_date") else None,
        "solar": str(item.get("solar", "")).strip() if item.get("solar") else None,
        "height": int(item["height"]) if item.get("height") else None,
        "weight": int(item["weight"]) if item.get("weight") else None,
    }


def _transform_team(item: Dict[str, Any]) -> Dict[str, Any]:
    """팀 데이터 변환"""
    return {
        "id": int(item["id"]),
        "team_code": str(item.get("team_code", "")).strip(),
        "region_name": str(item.get("region_name", "")).strip() if item.get("region_name") else None,
        "team_name": str(item.get("team_name", "")).strip(),
        "e_team_name": str(item.get("e_team_name", "")).strip() if item.get("e_team_name") else None,
        "orig_yyyy": str(item.get("orig_yyyy", "")).strip() if item.get("orig_yyyy") else None,
        "stadium_id": int(item["stadium_id"]) if item.get("stadium_id") else None,
        "zip_code1": str(item.get("zip_code1", "")).strip() if item.get("zip_code1") else None,
        "zip_code2": str(item.get("zip_code2", "")).strip() if item.get("zip_code2") else None,
        "address": str(item.get("address", "")).strip() if item.get("address") else None,
        "ddd": str(item.get("ddd", "")).strip() if item.get("ddd") else None,
        "tel": str(item.get("tel", "")).strip() if item.get("tel") else None,
        "fax": str(item.get("fax", "")).strip() if item.get("fax") else None,
        "homepage": str(item.get("homepage", "")).strip() if item.get("homepage") else None,
        "owner": str(item.get("owner", "")).strip() if item.get("owner") else None,
    }


def _transform_stadium(item: Dict[str, Any]) -> Dict[str, Any]:
    """경기장 데이터 변환"""
    return {
        "id": int(item["id"]),
        "stadium_code": str(item.get("stadium_code", "")).strip(),
        "statdium_name": str(item.get("statdium_name", "")).strip(),
        "hometeam_id": int(item["hometeam_id"]) if item.get("hometeam_id") else None,
        "hometeam_code": str(item.get("hometeam_code", "")).strip() if item.get("hometeam_code") else None,
        "seat_count": int(item["seat_count"]) if item.get("seat_count") else None,
        "address": str(item.get("address", "")).strip() if item.get("address") else None,
        "ddd": str(item.get("ddd", "")).strip() if item.get("ddd") else None,
        "tel": str(item.get("tel", "")).strip() if item.get("tel") else None,
    }


def _transform_schedule(item: Dict[str, Any]) -> Dict[str, Any]:
    """경기 일정 데이터 변환"""
    return {
        "id": int(item["id"]),
        "stadium_id": int(item["stadium_id"]),
        "hometeam_id": int(item["hometeam_id"]),
        "awayteam_id": int(item["awayteam_id"]),
        "stadium_code": str(item.get("stadium_code", "")).strip(),
        "sche_date": str(item.get("sche_date", "")).strip(),
        "gubun": str(item.get("gubun", "")).strip(),
        "hometeam_code": str(item.get("hometeam_code", "")).strip(),
        "awayteam_code": str(item.get("awayteam_code", "")).strip(),
        "home_score": int(item["home_score"]) if item.get("home_score") is not None else None,
        "away_score": int(item["away_score"]) if item.get("away_score") is not None else None,
    }
