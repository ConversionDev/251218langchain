"""
메일(mail_items) CRUD — 받은/보낸/임시보관/휴지통 공통.

상태 전이 (반드시 유지):
- 수신 직후:
  - Resolver 성공 → status=RECEIVED, ai_status=PENDING, folder=inbox
  - Resolver 실패 → status=REJECTED, ai_status=NULL, folder=rejected, spam_score=NULL (워커 미처리)
- 워커: PENDING → PROCESSING(commit) → AI 실행 → SUCCESS or FAILED(commit)
  - FAILED 시 retry_count+=1, last_failed_at, ai_result_raw 기록
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from infrastructure.persistence.models.mail_item_orm import MailItem  # type: ignore
from domain.models.enums.mail_enums import AiStatus, MailReceiveStatus  # type: ignore

# REJECTED 저장 시 owner_employee_id/folder placeholder (컬럼 NOT NULL 대응)
REJECTED_OWNER_PLACEHOLDER = "__rejected__"
REJECTED_FOLDER = "rejected"


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
        "receivedAt": row.received_at.isoformat() if row.received_at else None,
        "externalId": row.external_id,
        "status": row.status,
        "aiStatus": row.ai_status,
        "spamScore": row.spam_score,
        "processedAt": row.processed_at.isoformat() if row.processed_at else None,
        "retryCount": getattr(row, "retry_count", 0) or 0,
        "lastFailedAt": row.last_failed_at.isoformat() if row.last_failed_at else None,
        "aiResultRaw": row.ai_result_raw,
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


def list_starred(
    db: Session,
    owner_employee_id: str,
    limit: int = 500,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """소유자의 중요(별표) 메일을 폴더 무관하게 조회 (휴지통 제외)."""
    q = (
        db.query(MailItem)
        .filter(
            MailItem.owner_employee_id == owner_employee_id,
            MailItem.is_starred.is_(True),
            MailItem.folder != "trash",
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


def get_by_external_id(db: Session, external_id: str) -> Optional[Dict[str, Any]]:
    """external_id(Message-ID)로 메일 단건 조회. 수신 중복 판단용."""
    if not (external_id or "").strip():
        return None
    row = db.query(MailItem).filter(MailItem.external_id == external_id.strip()).first()
    return _row_to_dict(row) if row else None


def list_pending_for_worker(db: Session, limit: int = 1) -> List[Dict[str, Any]]:
    """
    워커용: status=RECEIVED, ai_status=PENDING 인 행을 limit 건 조회.
    SELECT ... FOR UPDATE SKIP LOCKED 로 잠금. 호출부에서 PROCESSING 으로 갱신 후 commit.
    """
    rows = (
        db.query(MailItem)
        .filter(
            MailItem.status == MailReceiveStatus.RECEIVED.value,
            MailItem.ai_status == AiStatus.PENDING.value,
        )
        .with_for_update(skip_locked=True)
        .order_by(MailItem.created_at.asc())
        .limit(limit)
        .all()
    )
    return [_row_to_dict(r) for r in rows]


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
    received_at: Optional[datetime] = None,
    external_id: Optional[str] = None,
    is_starred: bool = False,
    is_unread: bool = True,
    status: Optional[str] = None,
    ai_status: Optional[str] = None,
    spam_score: Optional[float] = None,
) -> Dict[str, Any]:
    """메일 1건 생성. 수신 건은 status/ai_status 사용. RECEIVED면 status=RECEIVED, ai_status=PENDING."""
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
        received_at=received_at if folder in ("inbox", REJECTED_FOLDER) else None,
        external_id=(external_id or "").strip() or None,
        status=status,
        ai_status=ai_status,
        spam_score=spam_score,
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
    ai_status: Optional[str] = None,
    spam_score: Optional[float] = None,
    processed_at: Optional[datetime] = None,
    retry_count: Optional[int] = None,
    last_failed_at: Optional[datetime] = None,
    ai_result_raw: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """메일 수정. 워커에서 ai_status, spam_score, folder, processed_at, retry_count, last_failed_at, ai_result_raw 반영."""
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
    if ai_status is not None:
        row.ai_status = ai_status
    if spam_score is not None:
        row.spam_score = spam_score
    if processed_at is not None:
        row.processed_at = processed_at
    if retry_count is not None:
        row.retry_count = retry_count
    if last_failed_at is not None:
        row.last_failed_at = last_failed_at
    if ai_result_raw is not None:
        row.ai_result_raw = ai_result_raw
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def move_to_trash(db: Session, id: str) -> Optional[Dict[str, Any]]:
    """메일을 휴지통으로 이동."""
    return update(db, id, folder="trash")


def reset_failed_to_pending(
    db: Session,
    id: str,
    *,
    max_retry_count: int = 3,
) -> Optional[Dict[str, Any]]:
    """FAILED 메일을 PENDING으로 되돌려 워커가 재처리하도록 함. retry_count <= max_retry_count 인 경우만."""
    row = db.get(MailItem, id)
    if not row:
        return None
    if row.ai_status != AiStatus.FAILED.value:
        return None
    if getattr(row, "retry_count", 0) or 0 > max_retry_count:
        return None
    row.ai_status = AiStatus.PENDING.value
    row.processed_at = None
    row.retry_count = 0
    row.last_failed_at = None
    row.ai_result_raw = None
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def delete_permanently(db: Session, id: str) -> bool:
    """메일 물리 삭제."""
    row = db.get(MailItem, id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
