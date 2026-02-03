"""
V10 임베딩 테이블 모델 (ExaOne 전용)

player / team / schedule / stadium 각각에 대응하는 임베딩 테이블 정의.
players, teams, stadiums, schedules와 동일한 Base.metadata를 사용하여 FK 해석이 정상 동작.

[생성 시점] Alembic 마이그레이션(add_exaone_embedding_tables)으로 생성.
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, text

from core.database import Base  # type: ignore

# 하위 호환: 동일 Base 사용
ExaOneEmbeddingMeta = Base.metadata
ExaOneEmbeddingBase = Base

VECTOR_DIM = 384


class PlayerEmbedding(Base):  # type: ignore[misc]
    """players 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "player_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    player_id = Column(BigInteger, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, comment="선수 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트 (to_embedding_text 결과)")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")


class TeamEmbedding(Base):  # type: ignore[misc]
    """teams 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "team_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    team_id = Column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, comment="팀 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")


class ScheduleEmbedding(Base):  # type: ignore[misc]
    """schedules 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "schedule_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    schedule_id = Column(BigInteger, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, comment="경기 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")


class StadiumEmbedding(Base):  # type: ignore[misc]
    """stadiums 테이블에 대응하는 임베딩 저장 (ExaOne 생성)."""

    __tablename__ = "stadium_embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    stadium_id = Column(BigInteger, ForeignKey("stadiums.id", ondelete="CASCADE"), nullable=False, comment="경기장 ID")
    content = Column(Text, nullable=False, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩")  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")
