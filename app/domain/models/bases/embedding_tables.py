"""
V10 임베딩 테이블 모델 (ExaOne 전용)

player / team / schedule / stadium 각각에 대응하는 임베딩 테이블 정의.

[생성 시점 · BP] Alembic 마이그레이션(add_exaone_embedding_tables)으로 생성.
env.py target_metadata에는 포함하지 않음(별도 Base). to_embedding_text 코드는 scripts/generate_soccer_embeddings + embedding_generator_service로 생성.
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, MetaData, Text, text
from sqlalchemy.orm import declarative_base

# ExaOne 전용 메타데이터 (Base.metadata와 분리 → Alembic이 관리하지 않음)
ExaOneEmbeddingMeta = MetaData()
ExaOneEmbeddingBase = declarative_base(metadata=ExaOneEmbeddingMeta)

VECTOR_DIM = 384


class PlayerEmbedding(ExaOneEmbeddingBase):  # type: ignore[misc]
    """players 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "player_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    player_id = Column(BigInteger, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, comment="선수 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트 (to_embedding_text 결과)")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")


class TeamEmbedding(ExaOneEmbeddingBase):  # type: ignore[misc]
    """teams 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "team_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    team_id = Column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, comment="팀 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")


class ScheduleEmbedding(ExaOneEmbeddingBase):  # type: ignore[misc]
    """schedules 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "schedule_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    schedule_id = Column(BigInteger, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, comment="경기 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")


class StadiumEmbedding(ExaOneEmbeddingBase):  # type: ignore[misc]
    """stadiums 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "stadium_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    stadium_id = Column(BigInteger, ForeignKey("stadiums.id", ondelete="CASCADE"), nullable=False, comment="경기장 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")
