"""disclosures, competency_anchors, performance_records에 tsvector 컬럼 + GIN 인덱스 추가.

하이브리드 검색(벡터 + BM25) 지원을 위한 PostgreSQL full-text search 인프라.
'simple' config: 한국어 형태소 분석 없이 공백/구두점 기준 토큰 분리.
GENERATED ALWAYS AS STORED: INSERT/UPDATE 시 자동 갱신.

Revision ID: 020_fulltext_search_tsvector
Revises: 019_audit_logs_table
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "020_fulltext_search_tsvector"
down_revision: Union[str, None] = "019_audit_logs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- disclosures ---
    col_exists = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'disclosures' AND column_name = 'tsv'"
        )
    ).fetchone()
    if not col_exists:
        op.execute(
            "ALTER TABLE disclosures ADD COLUMN tsv tsvector "
            "GENERATED ALWAYS AS ("
            "  to_tsvector('simple', coalesce(content, '') || ' ' || coalesce(section_title, ''))"
            ") STORED"
        )
    idx_exists = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_disclosures_tsv'"
        )
    ).fetchone()
    if not idx_exists:
        op.execute("CREATE INDEX idx_disclosures_tsv ON disclosures USING GIN(tsv)")

    # --- competency_anchors ---
    col_exists = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'competency_anchors' AND column_name = 'tsv'"
        )
    ).fetchone()
    if not col_exists:
        op.execute(
            "ALTER TABLE competency_anchors ADD COLUMN tsv tsvector "
            "GENERATED ALWAYS AS ("
            "  to_tsvector('simple', coalesce(content, '') || ' ' || coalesce(section_title, ''))"
            ") STORED"
        )
    idx_exists = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_competency_anchors_tsv'"
        )
    ).fetchone()
    if not idx_exists:
        op.execute("CREATE INDEX idx_competency_anchors_tsv ON competency_anchors USING GIN(tsv)")

    # --- performance_records ---
    col_exists = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'performance_records' AND column_name = 'tsv'"
        )
    ).fetchone()
    if not col_exists:
        op.execute(
            "ALTER TABLE performance_records ADD COLUMN tsv tsvector "
            "GENERATED ALWAYS AS ("
            "  to_tsvector('simple', coalesce(content, ''))"
            ") STORED"
        )
    idx_exists = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_performance_records_tsv'"
        )
    ).fetchone()
    if not idx_exists:
        op.execute("CREATE INDEX idx_performance_records_tsv ON performance_records USING GIN(tsv)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_performance_records_tsv")
    op.execute("ALTER TABLE performance_records DROP COLUMN IF EXISTS tsv")
    op.execute("DROP INDEX IF EXISTS idx_competency_anchors_tsv")
    op.execute("ALTER TABLE competency_anchors DROP COLUMN IF EXISTS tsv")
    op.execute("DROP INDEX IF EXISTS idx_disclosures_tsv")
    op.execute("ALTER TABLE disclosures DROP COLUMN IF EXISTS tsv")
