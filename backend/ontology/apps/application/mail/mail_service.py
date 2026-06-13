"""메일 유스케이스 — 수신/발송/임시보관/분류."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from core.config import get_settings  # type: ignore
from infrastructure.mail.send_mailgun import send_email as mailgun_send_email  # type: ignore
from infrastructure.orchestration import run_email_classify_and_record  # type: ignore
from infrastructure.persistence.repositories.employee_repository import get_by_id as employee_get_by_id  # type: ignore
from infrastructure.persistence.repositories.mail_item_repository import (  # type: ignore
    REJECTED_FOLDER,
    REJECTED_OWNER_PLACEHOLDER,
    create as mail_item_create,
    delete_permanently as mail_item_delete_permanently,
    get_by_external_id as mail_item_get_by_external_id,
    get_by_id as mail_item_get,
    list_by_folder as mail_item_list,
    move_to_trash as mail_item_trash,
    reset_failed_to_pending as mail_item_reset_failed_to_pending,
    update as mail_item_update,
)
from infrastructure.persistence.repositories.mail_owner_resolver import resolve_owner_by_to_email  # type: ignore
from domain.models.enums.mail_enums import AiStatus, MailReceiveStatus  # type: ignore

logger = logging.getLogger(__name__)


class MailService:

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_folder(
        self,
        folder: str,
        owner_employee_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        return mail_item_list(self.db, folder=folder, owner_employee_id=owner_employee_id, limit=limit, offset=offset)

    def get(self, mail_id: str) -> Optional[Dict[str, Any]]:
        return mail_item_get(self.db, mail_id)

    def receive_inbound(
        self,
        to_email: str,
        from_display: str,
        from_email: Optional[str],
        subject: str,
        body: Optional[str],
        message_id: Optional[str],
        received_at: datetime,
    ) -> Tuple[Dict[str, Any], str, int, bool]:
        """수신 1건 저장 (Store-then-Process).

        Returns: (record, folder, status_code, already_stored).
        """
        external_id = (message_id or "").strip() or None
        if external_id:
            existing = mail_item_get_by_external_id(self.db, external_id)
            if existing:
                return (existing, existing.get("folder") or "inbox", 200, True)

        owner = resolve_owner_by_to_email(self.db, to_email.strip())
        if not owner:
            record = mail_item_create(
                self.db,
                folder=REJECTED_FOLDER,
                owner_employee_id=REJECTED_OWNER_PLACEHOLDER,
                from_display=from_display or "",
                from_email=from_email,
                to_email=to_email.strip(),
                subject=subject or "",
                body=body,
                received_at=received_at,
                external_id=external_id,
                is_unread=True,
                status=MailReceiveStatus.REJECTED.value,
                ai_status=None,
                spam_score=None,
            )
            return (record, REJECTED_FOLDER, 200, False)

        record = mail_item_create(
            self.db,
            folder="inbox",
            owner_employee_id=owner,
            from_display=from_display or "",
            from_email=from_email,
            to_email=to_email.strip(),
            subject=subject or "",
            body=body,
            received_at=received_at,
            external_id=external_id,
            is_unread=True,
            status=MailReceiveStatus.RECEIVED.value,
            ai_status=AiStatus.PENDING.value,
            spam_score=None,
        )
        return (record, "inbox", 201, False)

    def send(
        self,
        sender_employee_id: str,
        to_id: str,
        to_email: str,
        to_display: str,
        subject: str,
        body: Optional[str],
    ) -> Dict[str, Any]:
        """메일 발송: 직원/사내 주소면 DB만, 외부 주소면 메일건 발송."""
        now = datetime.now(timezone.utc)
        sender = employee_get_by_id(self.db, sender_employee_id) if sender_employee_id else None
        from_display = (sender.get("name") or "me") if sender else "me"
        from_email = (sender.get("email") or "").strip() if sender else None

        recipient_owner_id = resolve_owner_by_to_email(self.db, to_email) if to_email else None

        record = mail_item_create(
            self.db,
            folder="sent",
            owner_employee_id=sender_employee_id,
            from_employee_id=sender_employee_id,
            from_display=from_display,
            from_email=from_email,
            to_address_id=to_id,
            to_display=to_display or to_id,
            to_email=to_email,
            subject=subject or "",
            body=body,
            sent_at=now,
            is_starred=False,
            is_unread=False,
        )

        if recipient_owner_id:
            mail_item_create(
                self.db,
                folder="inbox",
                owner_employee_id=recipient_owner_id,
                from_employee_id=sender_employee_id,
                from_display=from_display,
                from_email=from_email,
                to_address_id=to_id,
                to_display=to_display or to_id,
                to_email=to_email,
                subject=subject or "",
                body=body,
                received_at=now,
                is_starred=False,
                is_unread=True,
                status=MailReceiveStatus.RECEIVED.value,
                ai_status=AiStatus.SUCCESS.value,
                spam_score=0.0,
            )
        elif to_email:
            settings = get_settings()
            api_key = getattr(settings, "mailgun_api_key", None)
            domain = getattr(settings, "mailgun_domain", None)
            if api_key and domain:
                from_addr = from_email or f"noreply@{domain}"
                mailgun_send_email(
                    api_key=api_key,
                    domain=domain,
                    from_addr=from_addr,
                    to_addr=to_email,
                    subject=subject or "",
                    text=body or "",
                )

        return {"status": "success", "mail": record}

    def save_draft(
        self,
        owner_employee_id: str,
        draft_id: Optional[str],
        to_id: Optional[str],
        to_display: Optional[str],
        to_email: Optional[str],
        subject: str,
        body: Optional[str],
    ) -> Dict[str, Any]:
        if draft_id:
            row = mail_item_get(self.db, draft_id)
            if row and row.get("folder") == "draft":
                updated = mail_item_update(
                    self.db, draft_id,
                    subject=subject, body=body,
                    to_display=to_display, to_email=to_email, to_address_id=to_id,
                )
                return {"status": "saved", "mail": updated}
        record = mail_item_create(
            self.db,
            folder="draft",
            owner_employee_id=owner_employee_id,
            from_display="me",
            to_address_id=to_id,
            to_display=to_display,
            to_email=to_email,
            subject=subject or "",
            body=body,
            sent_at=None,
            is_unread=True,
        )
        return {"status": "saved", "mail": record}

    def update_flags(
        self,
        mail_id: str,
        is_starred: Optional[bool] = None,
        is_unread: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        return mail_item_update(self.db, mail_id, is_starred=is_starred, is_unread=is_unread)

    def delete(self, mail_id: str, permanent: bool = False) -> Dict[str, Any]:
        """삭제. permanent=True면 물리 삭제, 기본은 휴지통 이동.

        Raises ValueError if not found.
        """
        if permanent:
            if not mail_item_delete_permanently(self.db, mail_id):
                raise ValueError("Mail not found")
            return {"status": "deleted"}
        item = mail_item_trash(self.db, mail_id)
        if not item:
            raise ValueError("Mail not found")
        return {"status": "moved_to_trash", "mail": item}

    def retry_failed(self, mail_id: str) -> Dict[str, Any]:
        """FAILED 메일을 PENDING으로 전환.

        Raises ValueError if not found or retry limit exceeded.
        """
        item = mail_item_get(self.db, mail_id)
        if not item:
            raise ValueError("Mail not found")
        updated = mail_item_reset_failed_to_pending(self.db, mail_id, max_retry_count=3)
        if not updated:
            raise ValueError("Mail is not FAILED or retry_count exceeds limit (3). Cannot retry.")
        return {"status": "queued_for_retry", "mail": updated}

    def classify(
        self,
        subject: str,
        body: Optional[str],
        employee_id: str,
        period: Optional[str],
    ) -> Dict[str, Any]:
        """메일 분류 — 성과/5대 역량 판단 후 performance_records에 자동 기록."""
        return run_email_classify_and_record(
            self.db,
            subject=subject,
            body=body,
            employee_id=employee_id,
            period=period,
        )

