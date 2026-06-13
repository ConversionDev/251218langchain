"""감사 로그 저장/조회 리포지토리."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from infrastructure.persistence.models.audit_log_orm import AuditLog  # type: ignore


def _row_to_dict(row: AuditLog) -> Dict[str, Any]:
    return {
        "id": row.id,
        "entityType": row.entity_type,
        "entityId": row.entity_id,
        "action": row.action,
        "actor": row.actor,
        "reason": row.reason,
        "before": row.before_data,
        "after": row.after_data,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def create_log(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    before_data: Optional[Dict[str, Any]] = None,
    after_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        reason=reason,
        before_data=before_data,
        after_data=after_data,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def list_logs(
    db: Session,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    actor: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if actor:
        q = q.filter(AuditLog.actor == actor)
    if from_dt:
        q = q.filter(AuditLog.created_at >= from_dt)
    if to_dt:
        q = q.filter(AuditLog.created_at <= to_dt)
    rows = q.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(max(1, min(limit, 1000))).all()
    return [_row_to_dict(r) for r in rows]
