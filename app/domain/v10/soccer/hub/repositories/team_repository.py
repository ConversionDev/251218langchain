"""팀 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.v10.soccer.models.bases.team import Team  # type: ignore


class TeamRepository:
    """팀 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

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
        existing = db.query(Team).filter(Team.id == item["id"]).first()
        if existing:
            return False

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
        return True

    def save_batch(
        self,
        items: list[Dict[str, Any]],
        db: Session
    ) -> int:
        """
        팀 데이터를 배치로 저장합니다 (성능 최적화, Core INSERT).

        Args:
            items: 검증된 팀 데이터 딕셔너리 리스트
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
                    f"(:id_{idx}, :stadium_id_{idx}, :team_code_{idx}, :region_name_{idx}, "
                    f":team_name_{idx}, :e_team_name_{idx}, :orig_yyyy_{idx}, :zip_code1_{idx}, "
                    f":zip_code2_{idx}, :address_{idx}, :ddd_{idx}, :tel_{idx}, :fax_{idx}, "
                    f":homepage_{idx}, :owner_{idx})"
                )
                params[f"id_{idx}"] = item["id"]
                params[f"stadium_id_{idx}"] = item.get("stadium_id")
                params[f"team_code_{idx}"] = item.get("team_code", "")
                params[f"region_name_{idx}"] = item.get("region_name")
                params[f"team_name_{idx}"] = item.get("team_name", "")
                params[f"e_team_name_{idx}"] = item.get("e_team_name")
                params[f"orig_yyyy_{idx}"] = item.get("orig_yyyy")
                params[f"zip_code1_{idx}"] = item.get("zip_code1")
                params[f"zip_code2_{idx}"] = item.get("zip_code2")
                params[f"address_{idx}"] = item.get("address")
                params[f"ddd_{idx}"] = item.get("ddd")
                params[f"tel_{idx}"] = item.get("tel")
                params[f"fax_{idx}"] = item.get("fax")
                params[f"homepage_{idx}"] = item.get("homepage")
                params[f"owner_{idx}"] = item.get("owner")

            sql = text(f"""
                INSERT INTO teams (id, stadium_id, team_code, region_name, team_name, e_team_name, orig_yyyy, zip_code1, zip_code2, address, ddd, tel, fax, homepage, owner)
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
