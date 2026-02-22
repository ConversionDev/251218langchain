"""
성과 활동(performance_records) 저장·조회 — 통합 테이블 CRUD.

회의록·보고서·이메일을 한 테이블에서 분기별로 조회.
직원 제출(submit)은 id 자동 생성.
"""

import uuid
from typing import Any, Dict, List

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.models.bases.performance_record import PerformanceRecord  # type: ignore


def _row_to_dict(row: PerformanceRecord) -> Dict[str, Any]:
    """ORM 행 → API용 dict (camelCase)."""
    return {
        "id": row.id,
        "employeeId": row.employee_id,
        "period": row.period,
        "textType": row.text_type,
        "content": row.content,
        "tags": row.tags or [],
        "grade": row.grade,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def create(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """한 건 삽입. data: id, employeeId, period, textType, content, tags?, grade?."""
    record_id = data.get("id")
    if not record_id:
        raise ValueError("id required")
    existing = db.get(PerformanceRecord, record_id)
    if existing:
        raise ValueError(f"performance record already exists: {record_id}")

    row = PerformanceRecord(
        id=record_id,
        employee_id=data.get("employeeId") or data.get("employee_id", ""),
        period=data.get("period", ""),
        text_type=data.get("textType") or data.get("text_type", ""),
        content=data.get("content") or data.get("text", ""),
        tags=data.get("tags"),
        grade=data.get("grade"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def create_submission(
    db: Session,
    employee_id: str,
    text_type: str,
    content: str,
    period: str,
    tags: List[str] | None = None,
) -> Dict[str, Any]:
    """직원 제출 1건 (id 자동 생성). grade는 미설정(나중에 AI 분석)."""
    raw = (content or "").strip()
    if not raw:
        raise ValueError("content required")
    if text_type not in ("meeting", "report", "email"):
        raise ValueError("textType must be meeting, report, or email")
    record_id = f"SUB-{uuid.uuid4().hex[:14]}"
    row = PerformanceRecord(
        id=record_id,
        employee_id=employee_id,
        period=period,
        text_type=text_type,
        content=raw,
        tags=tags or [],
        grade=None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def list_by_employee(db: Session, employee_id: str, period: str | None = None, limit: int = 100) -> List[Dict[str, Any]]:
    """직원별 성과 기록 목록 (period 선택)."""
    q = db.query(PerformanceRecord).filter(PerformanceRecord.employee_id == employee_id)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    rows = q.order_by(PerformanceRecord.period.desc(), PerformanceRecord.id).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def list_all(db: Session, period: str | None = None, grade: str | None = None, limit: int = 5000) -> List[Dict[str, Any]]:
    """전체 목록 (period/grade 필터)."""
    q = db.query(PerformanceRecord)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    if grade:
        q = q.filter(PerformanceRecord.grade == grade)
    rows = q.order_by(PerformanceRecord.period, PerformanceRecord.employee_id).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def bulk_insert(db: Session, rows: List[Dict[str, Any]], skip_existing: bool = True) -> tuple[int, int]:
    """JSONL 행들을 bulk insert. 반환: (성공 수, 스킵 수)."""
    ids_in_file = [r.get("id") for r in rows if r.get("id")]
    existing_ids: set = set()
    if skip_existing and ids_in_file:
        existing = db.query(PerformanceRecord.id).filter(PerformanceRecord.id.in_(ids_in_file)).all()
        existing_ids = {x[0] for x in existing}
    to_add = []
    for r in rows:
        record_id = r.get("id")
        if not record_id:
            continue
        if record_id in existing_ids:
            continue
        content = (r.get("content") or r.get("text") or "").strip()
        to_add.append(
            PerformanceRecord(
                id=record_id,
                employee_id=r.get("employeeId") or r.get("employee_id", ""),
                period=r.get("period", ""),
                text_type=r.get("textType") or r.get("text_type", ""),
                content=content,
                tags=r.get("tags"),
                grade=r.get("grade"),
            )
        )
    for row in to_add:
        db.add(row)
    db.commit()
    return len(to_add), len(existing_ids)
