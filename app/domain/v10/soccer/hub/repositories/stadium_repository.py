"""경기장 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session

from domain.v10.member.bases.stadium import Stadium  # type: ignore

logger = logging.getLogger(__name__)


class StadiumRepository:
    """경기장 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def __init__(self):
        """StadiumRepository 초기화"""
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        item: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        검증된 경기장 데이터를 관계형 DB에 저장합니다.

        Args:
            item: 검증된 경기장 데이터 딕셔너리
            db: 데이터베이스 세션

        Returns:
            저장 성공 여부 (True: 저장됨, False: 건너뜀)
        """
        # 중복 체크
        existing = db.query(Stadium).filter(Stadium.id == item["id"]).first()
        if existing:
            self.logger.debug(
                f"[StadiumRepository] 경기장 ID {item.get('id')}는 이미 존재합니다. 건너뜁니다."
            )
            return False

        # 관계형 테이블에 저장
        stadium = Stadium(
            id=item["id"],
            stadium_code=item.get("stadium_code", ""),
            statdium_name=item.get("statdium_name", ""),
            hometeam_id=item.get("hometeam_id"),
            hometeam_code=item.get("hometeam_code"),
            seat_count=item.get("seat_count"),
            address=item.get("address"),
            ddd=item.get("ddd"),
            tel=item.get("tel"),
        )
        db.add(stadium)
        self.logger.debug(
            f"[StadiumRepository] 경기장 ID {item.get('id')} ({item.get('statdium_name')}) 관계형 DB에 저장됨"
        )
        return True
