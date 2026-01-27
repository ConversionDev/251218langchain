"""
V10 데이터 로더 - 유틸리티 함수

JSONL 파일 로드 및 데이터를 텍스트로 변환하는 유틸리티 함수를 제공합니다.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """JSONL 파일을 로드합니다."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[WARNING] JSON 파싱 오류 (건너뜀): {e}")
    return data


def player_to_text(item: Dict[str, Any]) -> str:
    """선수 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("player_name"):
        parts.append(f"선수 {item['player_name']}")

    if item.get("team_code"):
        parts.append(f"팀 코드: {item['team_code']}")

    if item.get("position"):
        position_map = {
            "GK": "골키퍼",
            "DF": "수비수",
            "MF": "미드필더",
            "FW": "공격수"
        }
        position_kr = position_map.get(item["position"], item["position"])
        parts.append(f"포지션: {position_kr} ({item['position']})")

    if item.get("back_no"):
        parts.append(f"등번호: {item['back_no']}번")

    if item.get("nation"):
        parts.append(f"국적: {item['nation']}")

    if item.get("join_yyyy"):
        parts.append(f"입단 연도: {item['join_yyyy']}년")

    if item.get("birth_date"):
        parts.append(f"생년월일: {item['birth_date']}")

    if item.get("height"):
        parts.append(f"키: {item['height']}cm")

    if item.get("weight"):
        parts.append(f"몸무게: {item['weight']}kg")

    if item.get("e_player_name"):
        parts.append(f"영문 이름: {item['e_player_name']}")

    if item.get("nickname"):
        parts.append(f"별명: {item['nickname']}")

    return ". ".join(parts) + "."


def team_to_text(item: Dict[str, Any]) -> str:
    """팀 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("team_name"):
        parts.append(f"팀 이름: {item['team_name']}")

    if item.get("e_team_name"):
        parts.append(f"영문 팀명: {item['e_team_name']}")

    if item.get("region_name"):
        parts.append(f"지역: {item['region_name']}")

    if item.get("team_code"):
        parts.append(f"팀 코드: {item['team_code']}")

    if item.get("orig_yyyy"):
        parts.append(f"창단 연도: {item['orig_yyyy']}년")

    if item.get("stadium_code"):
        parts.append(f"홈 경기장 코드: {item['stadium_code']}")

    if item.get("address"):
        parts.append(f"주소: {item['address']}")

    if item.get("tel"):
        parts.append(f"전화번호: {item['tel']}")

    if item.get("homepage"):
        parts.append(f"홈페이지: {item['homepage']}")

    if item.get("owner"):
        parts.append(f"구단주: {item['owner']}")

    return ". ".join(parts) + "."


def stadium_to_text(item: Dict[str, Any]) -> str:
    """경기장 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("statdium_name"):
        parts.append(f"경기장 이름: {item['statdium_name']}")

    if item.get("stadium_code"):
        parts.append(f"경기장 코드: {item['stadium_code']}")

    if item.get("hometeam_code"):
        parts.append(f"홈팀 코드: {item['hometeam_code']}")

    if item.get("seat_count"):
        parts.append(f"좌석 수: {item['seat_count']:,}석")

    if item.get("address"):
        parts.append(f"주소: {item['address']}")

    if item.get("tel"):
        parts.append(f"전화번호: {item['tel']}")

    if item.get("ddd"):
        parts.append(f"지역번호: {item['ddd']}")

    return ". ".join(parts) + "."


def schedule_to_text(item: Dict[str, Any]) -> str:
    """경기 일정 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("sche_date"):
        date_str = item["sche_date"]
        if len(date_str) == 8:
            formatted_date = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:8]}일"
            parts.append(f"경기 일자: {formatted_date}")
        else:
            parts.append(f"경기 일자: {date_str}")

    if item.get("stadium_code"):
        parts.append(f"경기장 코드: {item['stadium_code']}")

    if item.get("hometeam_code"):
        parts.append(f"홈팀 코드: {item['hometeam_code']}")

    if item.get("awayteam_code"):
        parts.append(f"원정팀 코드: {item['awayteam_code']}")

    if item.get("gubun"):
        gubun_map = {"Y": "정규 경기", "N": "비정규 경기"}
        parts.append(f"경기 구분: {gubun_map.get(item['gubun'], item['gubun'])}")

    if item.get("home_score") is not None and item.get("away_score") is not None:
        parts.append(
            f"경기 결과: {item['hometeam_code']} {item['home_score']} : "
            f"{item['away_score']} {item['awayteam_code']}"
        )

    return ". ".join(parts) + "."


