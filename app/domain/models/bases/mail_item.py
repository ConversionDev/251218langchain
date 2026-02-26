"""
메일 1건 (받은/보낸/임시보관/휴지통 공통).

mail_items 테이블. 폴더별로 동일 스키마 사용.
"""

from sqlalchemy import Boolean, Column, DateTime, String, Text, text

from core.database import Base  # type: ignore


class MailItem(Base):  # type: ignore[misc]
    """메일 1건. folder로 inbox/sent/draft/trash 구분."""

    __tablename__ = "mail_items"

    id = Column(String(64), primary_key=True, comment="메일 ID")
    folder = Column(String(16), nullable=False, index=True, comment="inbox | sent | draft | trash")
    owner_employee_id = Column(String(64), nullable=False, index=True, comment="메일함 소유자(직원 ID)")
    from_employee_id = Column(String(64), nullable=True, comment="발신 직원 ID")
    from_display = Column(String(256), nullable=False, server_default="", comment="발신자 표시명")
    from_email = Column(String(512), nullable=True, comment="발신자 이메일")
    to_address_id = Column(String(64), nullable=True, comment="수신자 주소록 ID")
    to_display = Column(String(256), nullable=True, comment="수신자 표시명")
    to_email = Column(String(512), nullable=True, comment="수신자 이메일")
    subject = Column(String(512), nullable=False, server_default="", comment="제목")
    body = Column(Text(), nullable=True, comment="본문")
    sent_at = Column(DateTime(), nullable=True, comment="발송 시각 (draft는 null)")
    is_starred = Column(Boolean(), nullable=False, server_default=text("false"), comment="중요 메일")
    is_unread = Column(Boolean(), nullable=False, server_default=text("true"), comment="읽지 않음")
    created_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="생성 시각")
    updated_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="수정 시각")
