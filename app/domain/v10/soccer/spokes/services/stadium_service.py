"""경기장 데이터 Rule 기반 처리 Service

명확한 규칙에 따라 검증된 데이터를 관계형 DB에 저장합니다.
Hub의 StadiumRepository를 사용합니다.
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from core.config import get_settings  # type: ignore
from domain.v10.soccer.hub.repositories.stadium_repository import StadiumRepository  # type: ignore


class StadiumService:
    """경기장 데이터 Rule 기반 처리 Service

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

    def process(
        self,
        data: List[Dict[str, Any]],
        db: Session | None = None,
        vector_store: Any = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        검증된 경기장 데이터를 관계형 DB에 저장합니다.

        Args:
            data: 검증된 경기장 데이터 리스트
            db: 데이터베이스 세션 (Rule 기반 저장용)
            vector_store: 미사용 (Rule 기반은 DB만 사용)
            auto_commit: True면 저장 후 commit, False면 호출자가 commit

        Returns:
            {"db": 저장된 개수, "vector": 0}
        """
        if not db or not data:
            return {"db": 0, "vector": 0}

        chunk_size = get_settings().db_batch_chunk_size
        repo = StadiumRepository()
        saved = repo.save_batch(data, db, chunk_size=chunk_size)
        if auto_commit:
            try:
                db.commit()
            except Exception:
                db.rollback()
                return {"db": 0, "vector": 0}
        return {"db": saved, "vector": 0}
