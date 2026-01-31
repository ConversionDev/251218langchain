"""경기 일정 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.v10.soccer.models.bases.schedule import Schedule  # type: ignore


class ScheduleRepository:
    """경기 일정 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

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
        existing = db.query(Schedule).filter(Schedule.id == item["id"]).first()
        if existing:
            return False

        schedule = Schedule(
            id=item["id"],
            stadium_id=item.get("stadium_id"),
            hometeam_id=item.get("hometeam_id"),
            awayteam_id=item.get("awayteam_id"),
            stadium_code=item.get("stadium_code", ""),
            sche_date=item.get("sche_date", ""),
            gubun=item.get("gubun", ""),
            hometeam_code=item.get("hometeam_code", ""),
            awayteam_code=item.get("awayteam_code", ""),
            home_score=item.get("home_score"),
            away_score=item.get("away_score"),
        )
        db.add(schedule)
        return True

    def save_batch(
        self,
        items: list[Dict[str, Any]],
        db: Session
    ) -> int:
        """
        경기 일정 데이터를 배치로 저장합니다 (성능 최적화, chunk 단위 처리).

        Args:
            items: 검증된 경기 일정 데이터 딕셔너리 리스트
            db: 데이터베이스 세션

        Returns:
            저장된 개수
        """
        if not items:
            return 0

        chunk_size = 100
        total_saved = 0

        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            try:
                values_list = []
                params = {}
                for idx, item in enumerate(chunk):
                    values_list.append(
                        f"(:id_{idx}, :stadium_id_{idx}, :hometeam_id_{idx}, :awayteam_id_{idx}, "
                        f":stadium_code_{idx}, :sche_date_{idx}, :gubun_{idx}, :hometeam_code_{idx}, "
                        f":awayteam_code_{idx}, :home_score_{idx}, :away_score_{idx})"
                    )
                    params[f"id_{idx}"] = item["id"]
                    params[f"stadium_id_{idx}"] = item.get("stadium_id")
                    params[f"hometeam_id_{idx}"] = item.get("hometeam_id")
                    params[f"awayteam_id_{idx}"] = item.get("awayteam_id")
                    params[f"stadium_code_{idx}"] = item.get("stadium_code", "")
                    params[f"sche_date_{idx}"] = item.get("sche_date", "")
                    params[f"gubun_{idx}"] = item.get("gubun", "")
                    params[f"hometeam_code_{idx}"] = item.get("hometeam_code", "")
                    params[f"awayteam_code_{idx}"] = item.get("awayteam_code", "")
                    params[f"home_score_{idx}"] = item.get("home_score")
                    params[f"away_score_{idx}"] = item.get("away_score")

                sql = text(f"""
                    INSERT INTO schedules (id, stadium_id, hometeam_id, awayteam_id, stadium_code, sche_date, gubun, hometeam_code, awayteam_code, home_score, away_score)
                    VALUES {', '.join(values_list)}
                    ON CONFLICT (id) DO NOTHING
                """)

                result = db.execute(sql, params)
                db.flush()
                total_saved += result.rowcount  # type: ignore[attr-defined]

            except IntegrityError:
                try:
                    db.rollback()
                except Exception:
                    pass
                continue
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass
                continue

        return total_saved
