"""
수신 메일 정규화 스키마.

공급자(Mailgun, SES 등)와 무관하게 우리 도메인이 사용하는 수신 1건 형식.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class NormalizedInboundMail:
    """공급자 독립 수신 메일 1건."""

    to_email: str
    from_display: str = ""
    from_email: Optional[str] = None
    subject: str = ""
    body: Optional[str] = None
    message_id: Optional[str] = None
    received_at: Optional[datetime] = None
