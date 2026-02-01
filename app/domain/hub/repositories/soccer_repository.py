"""
Soccer Repository — players, teams, stadiums, schedules 저장

규칙 기반 처리에서 관계형 DB 저장을 담당. 클래스명은 soccer 도메인에 맞춰
PlayerRepository, ScheduleRepository, StadiumRepository, TeamRepository 로 통일.
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from domain.models.bases.soccer import (  # type: ignore
    Player,
    Schedule,
    Stadium,
    Team,
)


def _dict_to_model_attrs(model_class: type, item: Dict[str, Any]) -> Dict[str, Any]:
    """ORM 컬럼명만 추려서 kwargs 생성."""
    cols = {c.key for c in model_class.__table__.columns}  # type: ignore[union-attr]
    return {k: v for k, v in item.items() if k in cols}


# -----------------------------------------------------------------------------
# Player
# -----------------------------------------------------------------------------


class PlayerRepository:
    """선수 저장 — soccer_repository 통일 이름."""

    def save(self, item: Dict[str, Any], db: Session) -> bool:
        """단건 저장/갱신."""
        attrs = _dict_to_model_attrs(Player, item)
        if not attrs:
            return False
        row = Player(**attrs)
        db.merge(row)
        return True

    def save_batch(
        self,
        data: List[Dict[str, Any]],
        db: Session,
        chunk_size: int = 500,
    ) -> int:
        """배치 저장. chunk_size 단위로 flush."""
        saved = 0
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            for item in chunk:
                if self.save(item, db):
                    saved += 1
            db.flush()
        return saved


# -----------------------------------------------------------------------------
# Schedule
# -----------------------------------------------------------------------------


class ScheduleRepository:
    """경기 일정 저장 — soccer_repository 통일 이름."""

    def save(self, item: Dict[str, Any], db: Session) -> bool:
        attrs = _dict_to_model_attrs(Schedule, item)
        if not attrs:
            return False
        row = Schedule(**attrs)
        db.merge(row)
        return True

    def save_batch(
        self,
        data: List[Dict[str, Any]],
        db: Session,
        chunk_size: int = 500,
    ) -> int:
        saved = 0
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            for item in chunk:
                if self.save(item, db):
                    saved += 1
            db.flush()
        return saved


# -----------------------------------------------------------------------------
# Stadium
# -----------------------------------------------------------------------------


class StadiumRepository:
    """경기장 저장 — soccer_repository 통일 이름."""

    def save(self, item: Dict[str, Any], db: Session) -> bool:
        attrs = _dict_to_model_attrs(Stadium, item)
        if not attrs:
            return False
        row = Stadium(**attrs)
        db.merge(row)
        return True

    def save_batch(
        self,
        data: List[Dict[str, Any]],
        db: Session,
        chunk_size: int = 500,
    ) -> int:
        saved = 0
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            for item in chunk:
                if self.save(item, db):
                    saved += 1
            db.flush()
        return saved


# -----------------------------------------------------------------------------
# Team
# -----------------------------------------------------------------------------


class TeamRepository:
    """팀 저장 — soccer_repository 통일 이름."""

    def save(self, item: Dict[str, Any], db: Session) -> bool:
        attrs = _dict_to_model_attrs(Team, item)
        if not attrs:
            return False
        row = Team(**attrs)
        db.merge(row)
        return True

    def save_batch(
        self,
        data: List[Dict[str, Any]],
        db: Session,
        chunk_size: int = 500,
    ) -> int:
        saved = 0
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            for item in chunk:
                if self.save(item, db):
                    saved += 1
            db.flush()
        return saved
