"""Soccer Spokes 서비스

엔티티 규칙 기반 서비스:
- 선수 데이터 규칙 기반 서비스 (PlayerService).
- 경기 일정 데이터 규칙 기반 서비스 (ScheduleService).
- 경기장 데이터 규칙 기반 서비스 (StadiumService).
- 팀 데이터 규칙 기반 서비스 (TeamService).

명확한 규칙에 따라 검증된 데이터를 관계형 DB에 저장합니다. Hub의 Repository를 사용합니다.
가이드: 업로드 직후 베이스 테이블의 embedding 컬럼을 채움 (단일 테이블).
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from core.config import get_settings  # type: ignore
from domain.hub.repositories import (  # type: ignore
    PlayerRepository,
    ScheduleRepository,
    StadiumRepository,
    TeamRepository,
)


def _fill_embeddings_after_save(db: Session, table_key: str) -> Dict[str, Any]:
    """저장 직후 embedding이 null인 행만 채움."""
    try:
        from domain.shared.embedding import get_embedding_model  # type: ignore
        from domain.spokes.soccer.services.embedding_service import fill_embeddings_for_entity  # type: ignore
        model = get_embedding_model(use_fp16=True)
        return fill_embeddings_for_entity(db, model, table_key)
    except Exception as e:
        return {"processed": 0, "failed": 0, "error": str(e)}


class PlayerService:
    """선수 데이터 Rule 기반 처리 Service.

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def process(
        self,
        data: List[Dict[str, Any]],
        db: Session | None = None,
        vector_store: Any = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """검증된 선수 데이터를 관계형 DB에 저장합니다."""
        if not db or not data:
            return {"db": 0, "vector": 0}
        chunk_size = get_settings().db_batch_chunk_size
        repo = PlayerRepository()
        saved = repo.save_batch(data, db, chunk_size=chunk_size)
        if auto_commit:
            try:
                db.commit()
                fill_result = _fill_embeddings_after_save(db, "players")
                return {"db": saved, "vector": fill_result.get("processed", 0)}
            except Exception:
                db.rollback()
                return {"db": 0, "vector": 0}
        return {"db": saved, "vector": 0}


class ScheduleService:
    """경기 일정 데이터 Rule 기반 처리 Service.

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def process(
        self,
        data: List[Dict[str, Any]],
        db: Session | None = None,
        vector_store: Any = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """검증된 경기 일정 데이터를 관계형 DB에 저장합니다."""
        if not db or not data:
            return {"db": 0, "vector": 0}
        chunk_size = get_settings().db_batch_chunk_size
        repo = ScheduleRepository()
        saved = repo.save_batch(data, db, chunk_size=chunk_size)
        if auto_commit:
            try:
                db.commit()
                fill_result = _fill_embeddings_after_save(db, "schedules")
                return {"db": saved, "vector": fill_result.get("processed", 0)}
            except Exception:
                db.rollback()
                return {"db": 0, "vector": 0}
        return {"db": saved, "vector": 0}


class StadiumService:
    """경기장 데이터 Rule 기반 처리 Service.

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def process(
        self,
        data: List[Dict[str, Any]],
        db: Session | None = None,
        vector_store: Any = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """검증된 경기장 데이터를 관계형 DB에 저장합니다."""
        if not db or not data:
            return {"db": 0, "vector": 0}
        chunk_size = get_settings().db_batch_chunk_size
        repo = StadiumRepository()
        saved = repo.save_batch(data, db, chunk_size=chunk_size)
        if auto_commit:
            try:
                db.commit()
                fill_result = _fill_embeddings_after_save(db, "stadiums")
                return {"db": saved, "vector": fill_result.get("processed", 0)}
            except Exception:
                db.rollback()
                return {"db": 0, "vector": 0}
        return {"db": saved, "vector": 0}


class TeamService:
    """팀 데이터 Rule 기반 처리 Service.

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def process(
        self,
        data: List[Dict[str, Any]],
        db: Session | None = None,
        vector_store: Any = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """검증된 팀 데이터를 관계형 DB에 저장합니다."""
        if not db or not data:
            return {"db": 0, "vector": 0}
        chunk_size = get_settings().db_batch_chunk_size
        repo = TeamRepository()
        saved = repo.save_batch(data, db, chunk_size=chunk_size)
        if auto_commit:
            try:
                db.commit()
                fill_result = _fill_embeddings_after_save(db, "teams")
                return {"db": saved, "vector": fill_result.get("processed", 0)}
            except Exception:
                db.rollback()
                return {"db": 0, "vector": 0}
        return {"db": saved, "vector": 0}
