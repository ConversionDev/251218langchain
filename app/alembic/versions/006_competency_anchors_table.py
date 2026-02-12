"""competency_anchors 테이블 + HNSW·btree 인덱스

Revision ID: 006_competency_anchors
Revises: 005_btree_disclosures
Create Date: 2026-02-09

- O*NET xlsx 4종 + NCS PDF 4종 통합 스키마. data/competency_anchors/README.md §7.
- 테이블 생성 후 HNSW(embedding), btree(category, level, category+level), unique(unique_id).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
except ImportError:
    Vector = None

revision: str = "006_competency_anchors"
down_revision: Union[str, None] = "005_btree_disclosures"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1024
HNSW_M = 24
HNSW_EF_CONSTRUCTION = 128


def upgrade() -> None:
    # 1. 테이블 생성
    if Vector is not None:
        op.create_table(
            "competency_anchors",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="PK"),
            sa.Column("content", sa.Text(), nullable=False, comment="한 문장/행동 지표 또는 능력·기술 설명"),
            sa.Column("embedding_content", sa.Text(), nullable=True, comment="임베딩용 텍스트"),
            sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)"),
            sa.Column("category", sa.Text(), nullable=True, comment="과제/능력/기술/업무스타일 또는 지식/기술/태도"),
            sa.Column("level", sa.Integer(), nullable=True, comment="숙련도·중요도 1~8"),
            sa.Column("section_title", sa.Text(), nullable=True, comment="능력단위명 또는 직무명"),
            sa.Column("source", sa.Text(), nullable=True, comment="출처 식별자"),
            sa.Column("source_type", sa.Text(), nullable=True, comment="ONET 또는 NCS"),
            sa.Column("metadata", JSONB(), nullable=True, comment="부가 정보 JSON"),
            sa.Column("unique_id", sa.Text(), nullable=True, comment="재적재/업서트용 고유 키"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        op.execute(
            "CREATE TABLE competency_anchors ("
            "id BIGSERIAL PRIMARY KEY, content TEXT NOT NULL, embedding_content TEXT, "
            "embedding vector(1024), category TEXT, level INTEGER, section_title TEXT, "
            "source TEXT, source_type TEXT, metadata JSONB, unique_id TEXT, "
            "created_at TIMESTAMP DEFAULT now())"
        )

    # 2. HNSW 인덱스 (BGE-m3 코사인 유사도)
    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_competency_anchors_embedding_hnsw
        ON competency_anchors
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION})
        """
    )
    # 3. btree 인덱스
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_competency_anchors_category "
        "ON competency_anchors USING btree (category)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_competency_anchors_level "
        "ON competency_anchors USING btree (level)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_competency_anchors_category_level "
        "ON competency_anchors USING btree (category, level)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_competency_anchors_unique_id "
        "ON competency_anchors (unique_id) WHERE unique_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_competency_anchors_unique_id")
    op.execute("DROP INDEX IF EXISTS idx_competency_anchors_category_level")
    op.execute("DROP INDEX IF EXISTS idx_competency_anchors_level")
    op.execute("DROP INDEX IF EXISTS idx_competency_anchors_category")
    op.execute("DROP INDEX IF EXISTS idx_competency_anchors_embedding_hnsw")
    op.drop_table("competency_anchors")
