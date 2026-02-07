"""공시(Disclosure) 단일 테이블 추가 (Soccer와 동일 가이드)

Revision ID: 002_disclosure
Revises: 001_initial
Create Date: 2026-02-07

disclosures: content, embedding_content, embedding vector(1024), source, page.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
except ImportError:
    Vector = None

revision: str = "002_disclosure"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1024


def upgrade() -> None:
    if Vector is not None:
        op.create_table(
            "disclosures",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="PK"),
            sa.Column("content", sa.Text(), nullable=False, comment="청크 본문"),
            sa.Column("embedding_content", sa.Text(), nullable=True, comment="임베딩용 텍스트"),
            sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)"),
            sa.Column("source", sa.Text(), nullable=True, comment="출처 예: ISO-30414-2018"),
            sa.Column("page", sa.Integer(), nullable=True, comment="페이지 번호"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        op.execute(
            "CREATE TABLE disclosures ("
            "id BIGSERIAL PRIMARY KEY, content TEXT NOT NULL, embedding_content TEXT, "
            "embedding vector(1024), source TEXT, page INTEGER, created_at TIMESTAMP DEFAULT now())"
        )


def downgrade() -> None:
    op.drop_table("disclosures")
