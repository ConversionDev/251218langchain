"""
Soccer 엔티티 → 임베딩/검색용 텍스트 변환

record(dict)를 RAG/벡터 검색용 자연어 문자열로 변환합니다.
"""

from typing import Any, Dict


def player_to_text(record: Dict[str, Any]) -> str:
    """선수 record를 임베딩용 텍스트로 변환."""
    parts = []
    if record.get("player_name"):
        parts.append(f"선수: {record['player_name']}")
    if record.get("e_player_name"):
        parts.append(f"영문명: {record['e_player_name']}")
    if record.get("position"):
        parts.append(f"포지션: {record['position']}")
    if record.get("back_no") is not None:
        parts.append(f"등번호: {record['back_no']}")
    if record.get("nation"):
        parts.append(f"국적: {record['nation']}")
    if record.get("join_yyyy"):
        parts.append(f"입단: {record['join_yyyy']}")
    if record.get("nickname"):
        parts.append(f"별명: {record['nickname']}")
    return " | ".join(parts) if parts else str(record)


def team_to_text(record: Dict[str, Any]) -> str:
    """팀 record를 임베딩용 텍스트로 변환."""
    parts = []
    if record.get("team_name"):
        parts.append(f"팀: {record['team_name']}")
    if record.get("e_team_name"):
        parts.append(f"영문명: {record['e_team_name']}")
    if record.get("region_name"):
        parts.append(f"지역: {record['region_name']}")
    if record.get("orig_yyyy"):
        parts.append(f"창단: {record['orig_yyyy']}")
    if record.get("team_code"):
        parts.append(f"코드: {record['team_code']}")
    return " | ".join(parts) if parts else str(record)


def schedule_to_text(record: Dict[str, Any]) -> str:
    """경기 일정 record를 임베딩용 텍스트로 변환."""
    parts = []
    if record.get("sche_date"):
        parts.append(f"경기일: {record['sche_date']}")
    if record.get("stadium_code"):
        parts.append(f"경기장코드: {record['stadium_code']}")
    if record.get("hometeam_code"):
        parts.append(f"홈팀: {record['hometeam_code']}")
    if record.get("awayteam_code"):
        parts.append(f"원정팀: {record['awayteam_code']}")
    if record.get("home_score") is not None and record.get("away_score") is not None:
        parts.append(f"스코어: {record['home_score']}-{record['away_score']}")
    return " | ".join(parts) if parts else str(record)


def stadium_to_text(record: Dict[str, Any]) -> str:
    """경기장 record를 임베딩용 텍스트로 변환."""
    parts = []
    name = record.get("statdium_name") or record.get("stadium_name")
    if name:
        parts.append(f"경기장: {name}")
    if record.get("stadium_code"):
        parts.append(f"코드: {record['stadium_code']}")
    if record.get("address"):
        parts.append(f"주소: {record['address']}")
    if record.get("seat_count") is not None:
        parts.append(f"좌석수: {record['seat_count']}")
    return " | ".join(parts) if parts else str(record)
