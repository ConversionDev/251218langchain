"""팀 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session

from domain.v10.member.bases.team import Team  # type: ignore

logger = logging.getLogger(__name__)


class TeamRepository:
    """팀 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def __init__(self):
        """TeamRepository 초기화"""
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        item: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        검증된 팀 데이터를 관계형 DB에 저장합니다.

        Args:
            item: 검증된 팀 데이터 딕셔너리
            db: 데이터베이스 세션

        Returns:
            저장 성공 여부 (True: 저장됨, False: 건너뜀)
        """
        # 중복 체크
        existing = db.query(Team).filter(Team.id == item["id"]).first()
        if existing:
            self.logger.debug(
                f"[TeamRepository] 팀 ID {item.get('id')}는 이미 존재합니다. 건너뜁니다."
            )
            return False

        # 관계형 테이블에 저장
        team = Team(
            id=item["id"],
            team_code=item.get("team_code", ""),
            region_name=item.get("region_name"),
            team_name=item.get("team_name", ""),
            e_team_name=item.get("e_team_name"),
            orig_yyyy=item.get("orig_yyyy"),
            stadium_id=item.get("stadium_id"),
            zip_code1=item.get("zip_code1"),
            zip_code2=item.get("zip_code2"),
            address=item.get("address"),
            ddd=item.get("ddd"),
            tel=item.get("tel"),
            fax=item.get("fax"),
            homepage=item.get("homepage"),
            owner=item.get("owner"),
        )
        db.add(team)
        self.logger.debug(
            f"[TeamRepository] 팀 ID {item.get('id')} ({item.get('team_name')}) 관계형 DB에 저장됨"
        )
        return True
