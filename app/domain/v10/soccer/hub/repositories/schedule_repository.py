"""경기 일정 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session

from domain.v10.member.bases.schedule import Schedule  # type: ignore
from domain.v10.member.bases.stadium import Stadium  # type: ignore
from domain.v10.member.bases.team import Team  # type: ignore

logger = logging.getLogger(__name__)


class ScheduleRepository:
    """경기 일정 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def __init__(self):
        """ScheduleRepository 초기화"""
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        item: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        검증된 경기 일정 데이터를 관계형 DB에 저장합니다.

        Args:
            item: 검증된 경기 일정 데이터 딕셔너리
            db: 데이터베이스 세션

        Returns:
            저장 성공 여부 (True: 저장됨, False: 건너뜀)
        """
        # Foreign Key 검증
        stadium_id = item.get("stadium_id")
        hometeam_id = item.get("hometeam_id")
        awayteam_id = item.get("awayteam_id")

        # stadium_id 검증
        if stadium_id:
            stadium_exists = db.query(Stadium).filter(Stadium.id == stadium_id).first()
            if not stadium_exists:
                self.logger.warning(
                    f"[ScheduleRepository] 경기 ID {item.get('id')}: "
                    f"stadium_id={stadium_id}가 stadiums 테이블에 존재하지 않아 관계형 DB에 저장할 수 없습니다."
                )
                return False

        # hometeam_id 검증
        if hometeam_id:
            hometeam_exists = db.query(Team).filter(Team.id == hometeam_id).first()
            if not hometeam_exists:
                self.logger.warning(
                    f"[ScheduleRepository] 경기 ID {item.get('id')}: "
                    f"hometeam_id={hometeam_id}가 teams 테이블에 존재하지 않아 관계형 DB에 저장할 수 없습니다."
                )
                return False

        # awayteam_id 검증
        if awayteam_id:
            awayteam_exists = db.query(Team).filter(Team.id == awayteam_id).first()
            if not awayteam_exists:
                self.logger.warning(
                    f"[ScheduleRepository] 경기 ID {item.get('id')}: "
                    f"awayteam_id={awayteam_id}가 teams 테이블에 존재하지 않아 관계형 DB에 저장할 수 없습니다."
                )
                return False

        # 중복 체크
        existing = db.query(Schedule).filter(Schedule.id == item["id"]).first()
        if existing:
            self.logger.debug(
                f"[ScheduleRepository] 경기 ID {item.get('id')}는 이미 존재합니다. 건너뜁니다."
            )
            return False

        # 관계형 테이블에 저장
        schedule = Schedule(
            id=item["id"],
            stadium_id=stadium_id,
            hometeam_id=hometeam_id,
            awayteam_id=awayteam_id,
            stadium_code=item.get("stadium_code", ""),
            sche_date=item.get("sche_date", ""),
            gubun=item.get("gubun", ""),
            hometeam_code=item.get("hometeam_code", ""),
            awayteam_code=item.get("awayteam_code", ""),
            home_score=item.get("home_score"),
            away_score=item.get("away_score"),
        )
        db.add(schedule)
        self.logger.debug(
            f"[ScheduleRepository] 경기 ID {item.get('id')} (날짜: {item.get('sche_date')}) 관계형 DB에 저장됨"
        )
        return True
