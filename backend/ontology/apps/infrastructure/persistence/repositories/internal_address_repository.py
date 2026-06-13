"""
사내 주소록(internal_addresses) — 공용 메일함·그룹 CRUD 및 목록.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.models.bases.internal_address import InternalAddress  # type: ignore


def _row_to_dict(row: InternalAddress) -> Dict[str, Any]:
    """ORM → API용 dict (camelCase)."""
    return {
        "id": row.id,
        "type": row.type,
        "displayName": row.display_name,
        "email": row.email,
        "department": row.department,
        "ownerEmployeeId": getattr(row, "owner_employee_id", None),
        "metadata": row.metadata_ or {},
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def list_all(db: Session, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """internal_addresses 전체 (type_filter: shared | group)."""
    q = db.query(InternalAddress).order_by(InternalAddress.type, InternalAddress.display_name)
    if type_filter and type_filter in ("shared", "group"):
        q = q.filter(InternalAddress.type == type_filter)
    return [_row_to_dict(r) for r in q.all()]


def get_by_id(db: Session, id: str) -> Optional[Dict[str, Any]]:
    """id로 단건 조회."""
    row = db.get(InternalAddress, id)
    return _row_to_dict(row) if row else None


def create(
    db: Session,
    type: str,
    display_name: str,
    email: str,
    department: Optional[str] = None,
    owner_employee_id: Optional[str] = None,
    metadata_: Optional[Dict[str, Any]] = None,
    id: Optional[str] = None,
) -> Dict[str, Any]:
    """공용·그룹 1건 생성. id 없으면 addr-{uuid} 자동 생성."""
    rid = (id or "").strip() or f"addr-{uuid.uuid4().hex[:12]}"
    if db.get(InternalAddress, rid):
        raise ValueError(f"internal_address already exists: {rid}")
    row = InternalAddress(
        id=rid,
        type=type.strip() or "shared",
        display_name=display_name.strip(),
        email=email.strip(),
        department=department.strip() if department else None,
        owner_employee_id=owner_employee_id.strip() if owner_employee_id else None,
        metadata_=metadata_,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def update(
    db: Session,
    id: str,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    department: Optional[str] = None,
    owner_employee_id: Optional[str] = None,
    metadata_: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """공용·그룹 1건 수정. 없으면 None."""
    row = db.get(InternalAddress, id)
    if not row:
        return None
    if display_name is not None:
        row.display_name = display_name.strip()
    if email is not None:
        row.email = email.strip()
    if department is not None:
        row.department = department.strip() or None
    if owner_employee_id is not None:
        row.owner_employee_id = owner_employee_id.strip() or None
    if metadata_ is not None:
        row.metadata_ = metadata_
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def delete_by_id(db: Session, id: str) -> bool:
    """공용·그룹 1건 삭제. 없으면 False."""
    row = db.get(InternalAddress, id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def upsert_from_dict(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """한 건 upsert (id 기준). JSONL import용."""
    row = db.get(InternalAddress, data.get("id") or data["id"])
    payload = {
        "type": (data.get("type") or data.get("type_", "")).strip() or "shared",
        "display_name": (data.get("display_name") or data.get("displayName", "")).strip(),
        "email": (data.get("email") or "").strip(),
        "department": (data.get("department") or "").strip() or None,
        "owner_employee_id": (data.get("owner_employee_id") or data.get("ownerEmployeeId") or "").strip() or None,
        "metadata_": data.get("metadata") or data.get("metadata_") or None,
    }
    if row:
        for k, v in payload.items():
            setattr(row, k, v)
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    new_row = InternalAddress(
        id=(data.get("id") or data["id"]).strip(),
        type=payload["type"],
        display_name=payload["display_name"],
        email=payload["email"],
        department=payload["department"],
        owner_employee_id=payload["owner_employee_id"],
        metadata_=payload["metadata_"],
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return _row_to_dict(new_row)
