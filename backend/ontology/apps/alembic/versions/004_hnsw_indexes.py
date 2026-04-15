"""embedding 컬럼에 HNSW 인덱스 적용 (BGE-m3 코사인 유사도)

Revision ID: 004_hnsw
Revises: 003_disclosure_meta
Create Date: 2026-02-09

- disclosures, stadiums, teams, players, schedules 의 embedding 에 HNSW 생성.
- vector_cosine_ops: BGE-m3 코사인 유사도 검색용.
- m=24, ef_construction=128: 복잡한 문서·높은 recall 권장값.
- 검색 시 정확도 우선이면: SET hnsw.ef_search = 100; (세션/앱에서 설정 가능)
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004_hnsw"
down_revision: Union[str, None] = "003_disclosure_meta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# HNSW 파라미터: recall·정확도 우선 (docs/vector-index-hnsw.md 참고)
HNSW_M = 24
HNSW_EF_CONSTRUCTION = 128

# (테이블명, 인덱스 이름)
INDEXES = [
    ("disclosures", "idx_disclosures_embedding_hnsw"),
    ("stadiums", "idx_stadiums_embedding_hnsw"),
    ("teams", "idx_teams_embedding_hnsw"),
    ("players", "idx_players_embedding_hnsw"),
    ("schedules", "idx_schedules_embedding_hnsw"),
]


def upgrade() -> None:
    for table_name, index_name in INDEXES:
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name}
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION})
            """
        )


def downgrade() -> None:
    for _table_name, index_name in INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {index_name}")
