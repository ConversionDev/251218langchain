"""
사내 주소록 1건 (공용 메일함·메일 그룹).

internal_addresses 테이블. person 타입은 employees에서 관리.
"""

from sqlalchemy import Column, DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base  # type: ignore


class InternalAddress(Base):  # type: ignore[misc]
    """공용 메일함(shared) 또는 메일 그룹(group) 1건."""

    __tablename__ = "internal_addresses"

    id = Column(String(64), primary_key=True, comment="주소 ID (예: addr-support)")
    type = Column(String(16), nullable=False, index=True, comment="shared | group")
    display_name = Column(String(256), nullable=False, comment="표시명")
    email = Column(String(512), nullable=False, comment="메일 주소")
    department = Column(String(128), nullable=True, comment="부서/용도")
    metadata_ = Column("metadata", JSONB(), nullable=True, comment="멤버 ID 목록 등 (group용)")
    created_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="생성 시각")
