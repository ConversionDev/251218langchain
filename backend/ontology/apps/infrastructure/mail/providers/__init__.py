"""수신 메일 공급자 인터페이스.

※ 여기서 MailgunProvider(구현)를 import 하지 않는다 — 그러면
   mailgun_adapter → providers.base → providers/__init__ → mailgun_adapter 의
   순환 import 가 생긴다. 구현(MailgunProvider)은 상위 infrastructure.mail.__init__ 에서만 노출.
"""

from infrastructure.mail.providers.base import InboundMailProvider  # type: ignore

__all__ = ["InboundMailProvider"]
