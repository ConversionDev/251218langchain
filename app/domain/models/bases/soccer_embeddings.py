"""Soccer 임베딩용 텍스트 변환 (player, team, schedule, stadium). Fallback: data_loader."""

from typing import Any, Dict

from domain.hub.shared.data_loader import (
    player_to_text,
    schedule_to_text,
    stadium_to_text,
    team_to_text,
)


def player_to_embedding_text(record: Dict[str, Any]) -> str:
    """선수 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return player_to_text(record)


def team_to_embedding_text(record: Dict[str, Any]) -> str:
    """팀 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return team_to_text(record)


def schedule_to_embedding_text(record: Dict[str, Any]) -> str:
    """경기 일정 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return schedule_to_text(record)


def stadium_to_embedding_text(record: Dict[str, Any]) -> str:
    """경기장 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return stadium_to_text(record)


def to_embedding_text(record: Dict[str, Any], entity_type: str) -> str:
    """entity_type에 따라 해당 변환 함수를 호출합니다."""
    if entity_type == "player":
        return player_to_embedding_text(record)
    if entity_type == "team":
        return team_to_embedding_text(record)
    if entity_type == "schedule":
        return schedule_to_embedding_text(record)
    if entity_type == "stadium":
        return stadium_to_embedding_text(record)
    raise ValueError(f"지원하지 않는 entity_type: {entity_type!r}")
