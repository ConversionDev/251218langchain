"""선수 데이터 관계형 DB 저장 Repository

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.v10.soccer.models.bases.player import Player  # type: ignore


class PlayerRepository:
    """선수 데이터 관계형 DB 저장 Repository

    규칙 기반 처리에서 관계형 DB에만 저장하는 책임을 가집니다.
    """

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
        existing = db.query(Player).filter(Player.id == item["id"]).first()
        if existing:
            return False

        player = Player(
            id=item["id"],
            team_id=item.get("team_id"),
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
        return True

    def save_batch(
        self,
        items: list[Dict[str, Any]],
        db: Session
    ) -> int:
        """
        선수 데이터를 배치로 저장합니다 (성능 최적화, chunk 단위 처리).

        Args:
            items: 검증된 선수 데이터 딕셔너리 리스트
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
                        f"(:id_{idx}, :team_id_{idx}, :player_name_{idx}, :e_player_name_{idx}, "
                        f":nickname_{idx}, :join_yyyy_{idx}, :position_{idx}, :back_no_{idx}, "
                        f":nation_{idx}, :birth_date_{idx}, :solar_{idx}, :height_{idx}, :weight_{idx})"
                    )
                    params[f"id_{idx}"] = item["id"]
                    params[f"team_id_{idx}"] = item.get("team_id")
                    params[f"player_name_{idx}"] = item.get("player_name", "")
                    params[f"e_player_name_{idx}"] = item.get("e_player_name")
                    params[f"nickname_{idx}"] = item.get("nickname")
                    params[f"join_yyyy_{idx}"] = str(item.get("join_yyyy")) if item.get("join_yyyy") else None
                    params[f"position_{idx}"] = item.get("position")
                    params[f"back_no_{idx}"] = item.get("back_no")
                    params[f"nation_{idx}"] = item.get("nation")
                    params[f"birth_date_{idx}"] = item.get("birth_date")
                    params[f"solar_{idx}"] = item.get("solar")
                    params[f"height_{idx}"] = item.get("height")
                    params[f"weight_{idx}"] = item.get("weight")

                sql = text(f"""
                    INSERT INTO players (id, team_id, player_name, e_player_name, nickname, join_yyyy, position, back_no, nation, birth_date, solar, height, weight)
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
