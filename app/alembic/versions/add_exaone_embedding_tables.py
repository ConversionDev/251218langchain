"""ExaOne 임베딩 테이블 추가 (BP: Alembic으로 일괄 관리)

Revision ID: add_exaone_emb
Revises: 5df98c0e25e0
Create Date: 2026-01-30

player_embeddings, team_embeddings, schedule_embeddings, stadium_embeddings 생성.
pgvector 확장 사용. 일반 테이블(players, teams, schedules, stadiums)과 동일하게 Alembic으로 관리.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
except ImportError:
    Vector = None  # fallback: raw SQL below

revision: str = "add_exaone_emb"
down_revision: Union[str, None] = "5df98c0e25e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # pgvector.sqlalchemy.Vector 사용 가능하면 op.create_table로, 아니면 raw SQL
    if Vector is not None:
        op.create_table(
            "player_embeddings",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="PK"),
            sa.Column("player_id", sa.BigInteger(), nullable=False, comment="선수 ID"),
            sa.Column("content", sa.Text(), nullable=False, comment="임베딩용 텍스트"),
            sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
            sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_table(
            "team_embeddings",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="PK"),
            sa.Column("team_id", sa.BigInteger(), nullable=False, comment="팀 ID"),
            sa.Column("content", sa.Text(), nullable=False, comment="임베딩용 텍스트"),
            sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_table(
            "schedule_embeddings",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="PK"),
            sa.Column("schedule_id", sa.BigInteger(), nullable=False, comment="경기 ID"),
            sa.Column("content", sa.Text(), nullable=False, comment="임베딩용 텍스트"),
            sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
            sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_table(
            "stadium_embeddings",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="PK"),
            sa.Column("stadium_id", sa.BigInteger(), nullable=False, comment="경기장 ID"),
            sa.Column("content", sa.Text(), nullable=False, comment="임베딩용 텍스트"),
            sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
            sa.ForeignKeyConstraint(["stadium_id"], ["stadiums.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        op.execute(
            "CREATE TABLE player_embeddings ("
            "id BIGSERIAL PRIMARY KEY, player_id BIGINT NOT NULL REFERENCES players(id) ON DELETE CASCADE, "
            "content TEXT NOT NULL, embedding vector(384), created_at TIMESTAMP DEFAULT now())"
        )
        op.execute(
            "CREATE TABLE team_embeddings ("
            "id BIGSERIAL PRIMARY KEY, team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE, "
            "content TEXT NOT NULL, embedding vector(384), created_at TIMESTAMP DEFAULT now())"
        )
        op.execute(
            "CREATE TABLE schedule_embeddings ("
            "id BIGSERIAL PRIMARY KEY, schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE, "
            "content TEXT NOT NULL, embedding vector(384), created_at TIMESTAMP DEFAULT now())"
        )
        op.execute(
            "CREATE TABLE stadium_embeddings ("
            "id BIGSERIAL PRIMARY KEY, stadium_id BIGINT NOT NULL REFERENCES stadiums(id) ON DELETE CASCADE, "
            "content TEXT NOT NULL, embedding vector(384), created_at TIMESTAMP DEFAULT now())"
        )


def downgrade() -> None:
    op.drop_table("stadium_embeddings")
    op.drop_table("schedule_embeddings")
    op.drop_table("team_embeddings")
    op.drop_table("player_embeddings")
