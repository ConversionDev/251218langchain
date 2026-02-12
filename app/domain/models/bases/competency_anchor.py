"""
역량 anchor 도메인 ORM — competency_anchors 단일 테이블 + embedding.

O*NET xlsx 4종 + NCS PDF 4종 통합 스키마. data/competency_anchors/README.md §7 참조.
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import BigInteger, Column, DateTime, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base  # type: ignore

from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore

VECTOR_DIM = BGE_M3_DENSE_DIM


class CompetencyAnchor(Base):  # type: ignore[misc]
    """역량 anchor 한 건. 과제/능력/기술/업무스타일 또는 NCS 수행준거."""

    __tablename__ = "competency_anchors"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    content = Column(Text, nullable=False, comment="한 문장/행동 지표 또는 능력·기술 설명")
    embedding_content = Column(Text, nullable=True, comment="임베딩용 텍스트 [category] [section_title]: content")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)")  # type: ignore[var-annotated]
    category = Column(Text, nullable=True, comment="과제/능력/기술/업무스타일 또는 지식/기술/태도")
    level = Column(Integer, nullable=True, comment="숙련도·중요도 1~8")
    section_title = Column(Text, nullable=True, comment="능력단위명 또는 직무명")
    source = Column(Text, nullable=True, comment="출처 식별자")
    source_type = Column(Text, nullable=True, comment="ONET 또는 NCS")
    metadata_ = Column("metadata", JSONB, nullable=True, comment="부가 정보 JSON")
    unique_id = Column(Text, nullable=True, comment="재적재/업서트용 고유 키")
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")
