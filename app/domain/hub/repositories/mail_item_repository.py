"""
메일(mail_items) CRUD — 받은/보낸/임시보관/휴지통 공통.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.models.bases.mail_item import MailItem  # type: ignore


def _row_to_dict(row: MailItem) -> Dict[str, Any]:
    """ORM → API/프론트 호환 dict (camelCase)."""
    return {
        "id": row.id,
        "folder": row.folder,
        "ownerEmployeeId": row.owner_employee_id,
        "fromEmployeeId": row.from_employee_id,
        "fromDisplay": row.from_display or "",
        "fromEmail": row.from_email,
        "toAddressId": row.to_address_id,
        "toDisplay": row.to_display,
        "toEmail": row.to_email,
        "subject": row.subject or "",
        "body": row.body,
        "sentAt": row.sent_at.isoformat() if row.sent_at else None,
        "isStarred": bool(row.is_starred),
        "isUnread": bool(row.is_unread),
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


def list_by_folder(
    db: Session,
    folder: str,
    owner_employee_id: str,
    limit: int = 500,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """폴더별 메일 목록 (소유자 기준). folder: inbox | sent | draft | trash."""
    q = (
        db.query(MailItem)
        .filter(
            MailItem.folder == folder,
            MailItem.owner_employee_id == owner_employee_id,
        )
        .order_by(MailItem.sent_at.desc().nullslast(), MailItem.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [_row_to_dict(r) for r in q.all()]


def get_by_id(db: Session, id: str) -> Optional[Dict[str, Any]]:
    """메일 단건 조회."""
    row = db.get(MailItem, id)
    return _row_to_dict(row) if row else None


def create(
    db: Session,
    folder: str,
    owner_employee_id: str,
    *,
    id: Optional[str] = None,
    from_employee_id: Optional[str] = None,
    from_display: str = "",
    from_email: Optional[str] = None,
    to_address_id: Optional[str] = None,
    to_display: Optional[str] = None,
    to_email: Optional[str] = None,
    subject: str = "",
    body: Optional[str] = None,
    sent_at: Optional[datetime] = None,
    is_starred: bool = False,
    is_unread: bool = True,
) -> Dict[str, Any]:
    """메일 1건 생성. id 없으면 mail-{uuid} 자동 생성."""
    rid = (id or "").strip() or f"mail-{uuid.uuid4().hex[:12]}"
    if db.get(MailItem, rid):
        rid = f"mail-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    row = MailItem(
        id=rid,
        folder=folder,
        owner_employee_id=owner_employee_id,
        from_employee_id=from_employee_id,
        from_display=from_display or "",
        from_email=from_email,
        to_address_id=to_address_id,
        to_display=to_display,
        to_email=to_email,
        subject=subject or "",
        body=body,
        sent_at=sent_at if folder == "sent" else None,
        is_starred=is_starred,
        is_unread=is_unread,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def update(
    db: Session,
    id: str,
    *,
    folder: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    to_display: Optional[str] = None,
    to_email: Optional[str] = None,
    to_address_id: Optional[str] = None,
    is_starred: Optional[bool] = None,
    is_unread: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """메일 수정 (임시보관 수정, 플래그 변경, 폴더 이동 등)."""
    row = db.get(MailItem, id)
    if not row:
        return None
    if folder is not None:
        row.folder = folder
    if subject is not None:
        row.subject = subject
    if body is not None:
        row.body = body
    if to_display is not None:
        row.to_display = to_display
    if to_email is not None:
        row.to_email = to_email
    if to_address_id is not None:
        row.to_address_id = to_address_id
    if is_starred is not None:
        row.is_starred = is_starred
    if is_unread is not None:
        row.is_unread = is_unread
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def move_to_trash(db: Session, id: str) -> Optional[Dict[str, Any]]:
    """메일을 휴지통으로 이동."""
    return update(db, id, folder="trash")


def delete_permanently(db: Session, id: str) -> bool:
    """메일 물리 삭제."""
    row = db.get(MailItem, id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
