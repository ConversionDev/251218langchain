"""
Soccer Store — 4개 테이블(players, teams, schedules, stadiums) 통합 벡터 저장

정책 기반 처리에서 벡터 스토어 저장은 이 모듈 하나만 사용합니다.
엔티티 타입별로 내부에서 분기합니다.
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.documents import Document  # type: ignore[import-untyped]

from domain.hub.shared.data_loader import (  # type: ignore
    player_to_text,
    schedule_to_text,
    stadium_to_text,
    team_to_text,
)

logger = logging.getLogger(__name__)

_ENTITY_TYPE = str  # "player" | "team" | "schedule" | "stadium"

_TO_TEXT = {
    "player": player_to_text,
    "team": team_to_text,
    "schedule": schedule_to_text,
    "stadium": stadium_to_text,
}


def _metadata_for(entity_type: _ENTITY_TYPE, item: Dict[str, Any]) -> Dict[str, Any]:
    """엔티티 타입별 메타데이터 추출 (None 제거)."""
    base = {"id": item.get("id"), "type": entity_type}
    if entity_type == "player":
        base.update({
            "team_id": item.get("team_id"),
            "player_name": item.get("player_name"),
            "position": item.get("position"),
            "back_no": item.get("back_no"),
            "nation": item.get("nation"),
            "join_yyyy": item.get("join_yyyy"),
        })
    elif entity_type == "team":
        base.update({
            "team_name": item.get("team_name"),
            "team_code": item.get("team_code"),
            "region_name": item.get("region_name"),
        })
    elif entity_type == "schedule":
        base.update({
            "sche_date": item.get("sche_date"),
            "stadium_id": item.get("stadium_id"),
            "hometeam_id": item.get("hometeam_id"),
            "awayteam_id": item.get("awayteam_id"),
        })
    elif entity_type == "stadium":
        base.update({
            "stadium_code": item.get("stadium_code"),
            "statdium_name": item.get("statdium_name") or item.get("stadium_name"),
            "address": item.get("address"),
        })
    return {k: v for k, v in base.items() if v is not None}


class SoccerStore:
    """4개 엔티티(player, team, schedule, stadium) 통합 벡터 스토어 저장.

    테이블은 4개 그대로 두고, 사용하는 곳은 이 클래스 하나만 씁니다.
    """

    def __init__(self, entity_type: _ENTITY_TYPE = "player") -> None:
        """
        Args:
            entity_type: "player" | "team" | "schedule" | "stadium"
        """
        self.entity_type = entity_type
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        item: Dict[str, Any],
        vector_store: Any,
        entity_type: Optional[_ENTITY_TYPE] = None,
    ) -> bool:
        """한 건 벡터 스토어에 저장.

        Args:
            item: 엔티티 딕셔너리
            vector_store: 벡터 스토어 인스턴스
            entity_type: 없으면 인스턴스 생성 시 지정한 값 사용
        """
        typ = entity_type or self.entity_type
        to_text = _TO_TEXT.get(typ)
        if not to_text:
            self.logger.error("[SoccerStore] 알 수 없는 entity_type: %s", typ)
            return False
        try:
            text = to_text(item)
            metadata = _metadata_for(typ, item)
            vector_store.add_documents([Document(page_content=text, metadata=metadata)])
            self.logger.debug("[SoccerStore] %s ID %s 벡터 스토어 저장됨", typ, item.get("id"))
            return True
        except Exception as e:
            self.logger.error("[SoccerStore] %s ID %s 저장 실패: %s", typ, item.get("id"), e)
            return False
