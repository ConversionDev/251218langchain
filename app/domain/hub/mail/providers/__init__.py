from domain.hub.mail.providers.base import InboundMailProvider  # type: ignore
from domain.hub.mail.providers.mailgun import MailgunProvider  # type: ignore

__all__ = ["InboundMailProvider", "MailgunProvider"]
