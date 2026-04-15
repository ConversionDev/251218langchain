"""메일 수신 공급자 계층. NormalizedInboundMail, parse_and_verify."""

from domain.hub.mail.schemas import NormalizedInboundMail  # type: ignore
from domain.hub.mail.providers.base import InboundMailProvider  # type: ignore
from domain.hub.mail.providers.mailgun import MailgunProvider  # type: ignore

__all__ = [
    "NormalizedInboundMail",
    "InboundMailProvider",
    "MailgunProvider",
]
