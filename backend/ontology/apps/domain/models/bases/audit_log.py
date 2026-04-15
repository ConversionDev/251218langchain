"""
감사 로그(Audit Log) ORM.

주요 액션(create/update/delete/status-change/analyze 등)의 증적을 append-only로 저장.
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base  # type: ignore


class AuditLog(Base):  # type: ignore[misc]
    """감사 로그 1건."""

    __tablename__ = "audit_logs"

    id = Column(Integer(), primary_key=True, autoincrement=True, comment="감사 로그 PK")
    entity_type = Column(String(64), nullable=False, index=True, comment="엔터티 타입 (예: employee)")
    entity_id = Column(String(128), nullable=False, index=True, comment="엔터티 ID (예: E001)")
    action = Column(String(64), nullable=False, index=True, comment="액션 (create/update/delete/analyze/onboard)")
    actor = Column(String(128), nullable=True, index=True, comment="수행자 식별자")
    reason = Column(Text(), nullable=True, comment="변경 사유")
    before_data = Column(JSONB(), nullable=True, comment="변경 전 데이터")
    after_data = Column(JSONB(), nullable=True, comment="변경 후 데이터")
    created_at = Column(DateTime(), server_default=text("now()"), nullable=False, index=True, comment="기록 시각")
