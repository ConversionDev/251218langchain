"""disclosures 테이블에 B-tree 인덱스 추가 (필터·중복 방지 가속)

Revision ID: 005_btree_disclosures
Revises: 004_hnsw
Create Date: 2026-02-09

- standard_type: WHERE standard_type = ANY(...) 필터 시 Full Table Scan 방지.
- (standard_type, page): 표준+페이지 조합 조회 시 복합 인덱스.
- unique_id: UNIQUE 인덱스로 중복 적재 방지 및 조회 가속.
- HNSW(벡터)와 함께 사용 시: B-tree로 후보 축소 → HNSW로 유사도 검색.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005_btree_disclosures"
down_revision: Union[str, None] = "004_hnsw"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 표준 타입 필터 인덱스 (가장 빈번한 조건)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_disclosures_standard_type "
        "ON disclosures USING btree (standard_type)"
    )
    # 2. 표준 + 페이지 복합 인덱스 (표준별·페이지별 조회 시)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_disclosures_standard_page "
        "ON disclosures USING btree (standard_type, page)"
    )
    # 3. 고유 ID 인덱스 (중복 적재 방지, 업서트/조회 시 활용)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_disclosures_unique_id "
        "ON disclosures (unique_id) WHERE unique_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_disclosures_unique_id")
    op.execute("DROP INDEX IF EXISTS idx_disclosures_standard_page")
    op.execute("DROP INDEX IF EXISTS idx_disclosures_standard_type")
