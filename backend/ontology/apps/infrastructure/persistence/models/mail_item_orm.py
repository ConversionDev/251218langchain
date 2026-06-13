"""
메일 1건 (받은/보낸/임시보관/휴지통 공통).

mail_items 테이블. 폴더별로 동일 스키마 사용.
- status: 수신 도메인 상태 (RECEIVED|REJECTED). REJECTED 시 ai_status/folder/spam_score NULL.
- ai_status: AI 처리 상태 (PENDING|PROCESSING|SUCCESS|FAILED). 코드에서는 domain.models.enums.mail_enums 사용.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, text

from core.database import Base  # type: ignore


class MailItem(Base):  # type: ignore[misc]
    """메일 1건. folder로 inbox/sent/draft/trash/spam 구분."""

    __tablename__ = "mail_items"

    id = Column(String(64), primary_key=True, comment="메일 ID")
    folder = Column(String(16), nullable=False, index=True, comment="inbox | sent | draft | trash | spam")
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
    received_at = Column(DateTime(), nullable=True, comment="수신 시각 (받은 메일용)")
    external_id = Column(String(512), nullable=True, unique=True, index=True, comment="Message-ID, 수신 중복 방지")
    # 수신·AI 상태 (Enum value 저장. AiStatus, MailReceiveStatus 사용)
    status = Column(String(16), nullable=True, comment="수신 도메인: RECEIVED | REJECTED")
    ai_status = Column(String(16), nullable=True, index=True, server_default=text("'PENDING'"), comment="AI 처리: PENDING|PROCESSING|SUCCESS|FAILED")
    spam_score = Column(Float(), nullable=True, comment="LLaMA 스팸 점수 (0~1)")
    processed_at = Column(DateTime(), nullable=True, comment="워커 처리 완료 시각")
    retry_count = Column(Integer(), nullable=False, server_default=text("0"), comment="AI 실패 재시도 횟수")
    last_failed_at = Column(DateTime(), nullable=True, comment="마지막 AI 실패 시각")
    ai_result_raw = Column(Text(), nullable=True, comment="실패 시 에러 메시지 또는 AI 원시 응답")
    is_starred = Column(Boolean(), nullable=False, server_default=text("false"), comment="중요 메일")
    is_unread = Column(Boolean(), nullable=False, server_default=text("true"), comment="읽지 않음")
    created_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="생성 시각")
    updated_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="수정 시각")
