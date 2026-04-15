"""
Mailgun 수신 Webhook 어댑터.

- multipart/form-data 필드: recipient, sender, subject, body-plain, Message-Id, timestamp, token, signature
- HMAC-SHA256: timestamp + token 을 Signing Key로 서명 후 signature 와 비교
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.config import get_settings  # type: ignore
from domain.hub.mail.schemas import NormalizedInboundMail  # type: ignore
from domain.hub.mail.providers.base import InboundMailProvider  # type: ignore

logger = logging.getLogger(__name__)


class MailgunProvider(InboundMailProvider):
    """Mailgun Webhook: parse_and_verify(payload_dict) -> NormalizedInboundMail."""

    def parse_and_verify(self, request_or_payload: Any) -> NormalizedInboundMail:
        """
        payload: Mailgun form 필드가 이미 파싱된 dict.
          키: recipient, sender, subject, body-plain, Message-Id, timestamp, token, signature 등.
        검증 실패 시 ValueError.
        """
        if isinstance(request_or_payload, dict):
            payload = request_or_payload
        else:
            raise ValueError("MailgunProvider expects a dict (parsed form payload)")

        settings = get_settings()
        if not settings.mailgun_skip_verify:
            key = (settings.mailgun_webhook_signing_key or "").strip()
            if not key:
                raise ValueError("mailgun_webhook_signing_key required when mailgun_skip_verify is False")
            self._verify_signature(payload, key)

        return self._parse(payload)

    def _verify_signature(self, payload: Dict[str, Any], signing_key: str) -> None:
        """HMAC-SHA256: signed = HMAC(signing_key, timestamp + token). Compare with signature."""
        timestamp = payload.get("timestamp") or ""
        token = payload.get("token") or ""
        signature = (payload.get("signature") or "").strip()
        if not timestamp or not token or not signature:
            raise ValueError("Missing timestamp, token, or signature for Mailgun verification")
        expected = hmac.new(
            signing_key.encode("utf-8"),
            msg=f"{timestamp}{token}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("Mailgun signature verification failed")

    def _parse(self, payload: Dict[str, Any]) -> NormalizedInboundMail:
        recipient = (payload.get("recipient") or "").strip()
        sender = (payload.get("sender") or "").strip()
        subject = (payload.get("subject") or "").strip()
        body = payload.get("body-plain")
        if body is not None and isinstance(body, str):
            body = body.strip() or None
        message_id = payload.get("Message-Id") or payload.get("message-id")
        if message_id is not None and isinstance(message_id, str):
            message_id = message_id.strip() or None
        received_at: Optional[datetime] = None
        ts = payload.get("Date") or payload.get("timestamp")
        if ts:
            try:
                if isinstance(ts, (int, float)):
                    received_at = datetime.fromtimestamp(float(ts), tz=timezone.utc)
                elif isinstance(ts, str) and ts.strip():
                    received_at = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        if received_at is None:
            received_at = datetime.now(timezone.utc)

        return NormalizedInboundMail(
            to_email=recipient or "",
            from_display=sender,
            from_email=sender if "@" in sender else None,
            subject=subject,
            body=body,
            message_id=message_id,
            received_at=received_at,
        )
