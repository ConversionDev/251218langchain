"""
공시(Disclosure) 도메인 ORM — 단일 테이블 + embedding.

disclosures: content, embedding_content([Standard][Section]: Content), embedding,
  source, page, standard_type, section_title, metadata(JSON), unique_id.
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import BigInteger, Column, DateTime, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base  # type: ignore

from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore

VECTOR_DIM = BGE_M3_DENSE_DIM


class Disclosure(Base):  # type: ignore[misc]
    """공시 문서 청크. ISO 30414, IFRS S1/S2, OECD 등."""

    __tablename__ = "disclosures"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="PK")
    content = Column(Text, nullable=False, comment="청크 본문")
    embedding_content = Column(Text, nullable=True, comment="[Standard] [Section]: Content 형태로 임베딩")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)")  # type: ignore[var-annotated]
    source = Column(Text, nullable=True, comment="출처 파일 식별자 예: 2018-ISO-30414")
    page = Column(Integer, nullable=True, comment="페이지 번호")
    standard_type = Column(Text, nullable=True, comment="ISO30414, IFRS_S1, IFRS_S2, OECD 등")
    section_title = Column(Text, nullable=True, comment="조항/섹션 제목")
    metadata_ = Column("metadata", JSONB, nullable=True, comment="페이지·발행연도 등 JSON")
    unique_id = Column(Text, nullable=True, comment="재적재/업서트용 고유 키")
    created_at = Column(DateTime, server_default=text("now()"), nullable=True, comment="생성 시각")
