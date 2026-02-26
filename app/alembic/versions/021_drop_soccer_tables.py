"""Soccer 도메인 테이블 및 HNSW 인덱스 제거.

Revision ID: 021_drop_soccer
Revises: 020_fulltext_search_tsvector
Create Date: 2026-02-26

- soccer 관련 기능 제거에 따라 players, teams, stadiums, schedules 테이블과
  해당 embedding HNSW 인덱스를 삭제합니다.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "021_drop_soccer"
down_revision: Union[str, None] = "020_fulltext_search_tsvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 004_hnsw_indexes에서 생성한 soccer 테이블 HNSW 인덱스
SOCCER_INDEXES = [
    "idx_stadiums_embedding_hnsw",
    "idx_teams_embedding_hnsw",
    "idx_players_embedding_hnsw",
    "idx_schedules_embedding_hnsw",
]


def upgrade() -> None:
    for index_name in SOCCER_INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {index_name}")

    # 자식 테이블 먼저 삭제 후, 순환 FK 제거, 부모 테이블 삭제. IF EXISTS로 재실행 시 오류 방지.
    op.execute("DROP TABLE IF EXISTS schedules CASCADE")
    op.execute("DROP TABLE IF EXISTS players CASCADE")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'stadiums') THEN
        ALTER TABLE stadiums DROP CONSTRAINT IF EXISTS stadiums_hometeam_id_fkey;
      END IF;
      IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'teams') THEN
        ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_stadium_id_fkey;
      END IF;
    END $$;
    """)
    op.execute("DROP TABLE IF EXISTS teams CASCADE")
    op.execute("DROP TABLE IF EXISTS stadiums CASCADE")


def downgrade() -> None:
    # soccer 도메인 제거로 복원하지 않음 (필요 시 001_initial_squashed, 004_hnsw_indexes 참고)
    pass
