"""메일 인프라 어댑터 (수신 웹훅·발송).

domain/hub/mail 에서 이동 (Phase 4 완성). 외부 메일 시스템(Mailgun) 연동 어댑터.
- 수신: MailgunProvider.parse_and_verify (HMAC 검증) → NormalizedInboundMail
- 발송: send_email
"""

from infrastructure.mail.schemas import NormalizedInboundMail  # type: ignore
from infrastructure.mail.providers.base import InboundMailProvider  # type: ignore
from infrastructure.mail.mailgun_adapter import MailgunProvider  # type: ignore
from infrastructure.mail.send_mailgun import send_email  # type: ignore

__all__ = [
    "NormalizedInboundMail",
    "InboundMailProvider",
    "MailgunProvider",
    "send_email",
]
