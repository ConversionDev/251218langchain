"""선수 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session

from domain.v10.member.bases.player import Player  # type: ignore
from domain.v10.member.bases.team import Team  # type: ignore

logger = logging.getLogger(__name__)


class PlayerRepository:
    """선수 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def __init__(self):
        """PlayerRepository 초기화"""
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        item: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        검증된 선수 데이터를 관계형 DB에 저장합니다.

        Args:
            item: 검증된 선수 데이터 딕셔너리
            db: 데이터베이스 세션

        Returns:
            저장 성공 여부 (True: 저장됨, False: 건너뜀)
        """
        team_id = item.get("team_id")

        # team_id가 없으면 저장 불가
        if not team_id:
            self.logger.warning(
                f"[PlayerRepository] 선수 ID {item.get('id')} ({item.get('player_name', 'Unknown')}): "
                f"team_id가 없어 관계형 DB에 저장할 수 없습니다."
            )
            return False

        # team_id가 teams 테이블에 존재하는지 확인
        team_exists = db.query(Team).filter(Team.id == team_id).first()
        if not team_exists:
            self.logger.warning(
                f"[PlayerRepository] 선수 ID {item.get('id')} ({item.get('player_name', 'Unknown')}): "
                f"team_id={team_id}가 teams 테이블에 존재하지 않아 관계형 DB에 저장할 수 없습니다."
            )
            return False

        # 중복 체크
        existing = db.query(Player).filter(Player.id == item["id"]).first()
        if existing:
            self.logger.debug(
                f"[PlayerRepository] 선수 ID {item.get('id')}는 이미 존재합니다. 건너뜁니다."
            )
            return False

        # 관계형 테이블에 저장
        player = Player(
            id=item["id"],
            team_id=team_id,
            player_name=item.get("player_name", ""),
            e_player_name=item.get("e_player_name"),
            nickname=item.get("nickname"),
            join_yyyy=str(item.get("join_yyyy")) if item.get("join_yyyy") else None,
            position=item.get("position"),
            back_no=item.get("back_no"),
            nation=item.get("nation"),
            birth_date=item.get("birth_date"),
            solar=item.get("solar"),
            height=item.get("height"),
            weight=item.get("weight"),
        )
        db.add(player)
        self.logger.debug(
            f"[PlayerRepository] 선수 ID {item.get('id')} ({item.get('player_name')}) 관계형 DB에 저장됨"
        )
        return True
