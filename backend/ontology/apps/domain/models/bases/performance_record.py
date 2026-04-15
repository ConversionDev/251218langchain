"""
성과 활동 1건 (통합: 회의록·보고서·이메일).

performance_records 테이블. 분기별 실적/활동 조회 및 AI 성장 분석용.
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import Column, DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base  # type: ignore
from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore


class PerformanceRecord(Base):  # type: ignore[misc]
    """한 직원의 한 분기·한 텍스트 유형 1건."""

    __tablename__ = "performance_records"

    id = Column(String(64), primary_key=True, comment="레코드 ID (예: PF0001)")
    employee_id = Column(String(64), nullable=False, index=True, comment="직원 ID")
    period = Column(String(32), nullable=False, index=True, comment="분기 (2025-Q1 등)")
    text_type = Column(String(32), nullable=False, index=True, comment="meeting|report|email")
    content = Column(Text(), nullable=False, comment="본문 텍스트")
    tags = Column(JSONB(), nullable=True, comment="태그 배열")
    grade = Column(String(32), nullable=True, index=True, comment="high|normal")
    created_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="생성 시각")
    embedding_content = Column(Text(), nullable=True, comment="RAG 임베딩용 텍스트 (직원명·분기·유형·본문 요약)")
    embedding = Column(pgvector.sqlalchemy.Vector(BGE_M3_DENSE_DIM), nullable=True, comment="BGE-m3 1024차원, RAG 검색용")  # type: ignore[var-annotated]
