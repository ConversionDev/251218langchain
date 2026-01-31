"""경기장 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.v10.soccer.models.bases.stadium import Stadium  # type: ignore


class StadiumRepository:
    """경기장 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

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
        existing = db.query(Stadium).filter(Stadium.id == item["id"]).first()
        if existing:
            return False

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
        return True

    def save_batch(
        self,
        items: list[Dict[str, Any]],
        db: Session
    ) -> int:
        """
        경기장 데이터를 배치로 저장합니다 (성능 최적화, Core INSERT).

        Args:
            items: 검증된 경기장 데이터 딕셔너리 리스트
            db: 데이터베이스 세션

        Returns:
            저장된 개수
        """
        if not items:
            return 0

        try:
            values_list = []
            params = {}
            for idx, item in enumerate(items):
                values_list.append(
                    f"(:id_{idx}, :stadium_code_{idx}, :statdium_name_{idx}, :hometeam_id_{idx}, "
                    f":hometeam_code_{idx}, :seat_count_{idx}, :address_{idx}, :ddd_{idx}, :tel_{idx})"
                )
                params[f"id_{idx}"] = item["id"]
                params[f"stadium_code_{idx}"] = item.get("stadium_code", "")
                params[f"statdium_name_{idx}"] = item.get("statdium_name", "")
                params[f"hometeam_id_{idx}"] = item.get("hometeam_id")
                params[f"hometeam_code_{idx}"] = item.get("hometeam_code")
                params[f"seat_count_{idx}"] = item.get("seat_count")
                params[f"address_{idx}"] = item.get("address")
                params[f"ddd_{idx}"] = item.get("ddd")
                params[f"tel_{idx}"] = item.get("tel")

            sql = text(f"""
                INSERT INTO stadiums (id, stadium_code, statdium_name, hometeam_id, hometeam_code, seat_count, address, ddd, tel)
                VALUES {', '.join(values_list)}
                ON CONFLICT (id) DO NOTHING
            """)

            result = db.execute(sql, params)
            db.flush()
            return result.rowcount  # type: ignore[attr-defined]

        except IntegrityError:
            try:
                db.rollback()
            except Exception:
                pass
            return 0
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
            return 0
