"""성과 활동 API — performance_records 통합 테이블.

관리자: GET 목록, GET by-employee, GET 단건
직원 워크스페이스: POST submit, GET my (본인 제출 목록)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from core.database import get_db  # type: ignore
from infrastructure.persistence.repositories.performance_record_repository import (  # type: ignore
    create_submission as repo_create_submission,
    list_by_employee,
)
from domain.models.bases.performance_record import PerformanceRecord  # type: ignore

router = APIRouter(prefix="/activity-records", tags=["Activity Records (성과 활동)"])


class ActivityListResponse(BaseModel):
    """활동 목록 응답."""
    items: List[Dict[str, Any]]
    total: int


def _row_to_dict(row: PerformanceRecord) -> Dict[str, Any]:
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


@router.get("", response_model=ActivityListResponse)
def get_activity_records(
    period: Optional[str] = Query(None, description="분기 필터 (예: 2025-Q1)"),
    grade: Optional[str] = Query(None, description="high|normal"),
    text_type: Optional[str] = Query(None, alias="textType", description="meeting|report|email"),
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db),
) -> ActivityListResponse:
    """성과 활동 목록 (필터 가능)."""
    q = db.query(PerformanceRecord)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    if grade:
        q = q.filter(PerformanceRecord.grade == grade)
    if text_type:
        q = q.filter(PerformanceRecord.text_type == text_type)
    total = q.count()
    rows = q.order_by(PerformanceRecord.period.desc(), PerformanceRecord.id).limit(limit).all()
    return ActivityListResponse(items=[_row_to_dict(r) for r in rows], total=total)


@router.get("/by-employee/{employee_id}", response_model=List[Dict[str, Any]])
def get_activities_by_employee(
    employee_id: str,
    period: Optional[str] = Query(None, description="분기 필터"),
    text_type: Optional[str] = Query(None, alias="textType", description="meeting|report|email"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """사원별 성과 활동 목록."""
    q = db.query(PerformanceRecord).filter(PerformanceRecord.employee_id == employee_id)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    if text_type:
        q = q.filter(PerformanceRecord.text_type == text_type)
    rows = q.order_by(PerformanceRecord.period.desc(), PerformanceRecord.text_type).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


@router.get("/my", response_model=List[Dict[str, Any]])
def get_my_activities(
    employeeId: str = Query(..., alias="employeeId", description="직원 ID (워크스페이스 본인)"),
    period: Optional[str] = Query(None),
    textType: Optional[str] = Query(None, description="meeting|report|email"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """직원 본인 제출 목록 (워크스페이스용)."""
    q = db.query(PerformanceRecord).filter(PerformanceRecord.employee_id == employeeId)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    if textType:
        q = q.filter(PerformanceRecord.text_type == textType)
    rows = q.order_by(PerformanceRecord.period.desc(), PerformanceRecord.id).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


class SubmitPayload(BaseModel):
    """직원 업무 제출 요청."""
    employeeId: str = Field(..., description="직원 ID")
    textType: str = Field(..., description="meeting | report | email")
    content: str = Field(..., min_length=1, description="본문")
    period: str = Field(..., description="분기 (예: 2025-Q1)")
    tags: List[str] = Field(default_factory=list, description="태그")


@router.post("/submit", response_model=Dict[str, Any], status_code=201)
def submit_activity(payload: SubmitPayload, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원 업무 제출 (회의록·보고서·이메일)."""
    try:
        return repo_create_submission(
            db,
            employee_id=payload.employeeId,
            text_type=payload.textType,
            content=payload.content,
            period=payload.period,
            tags=payload.tags or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{record_id}", response_model=Dict[str, Any])
def get_activity_record(record_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """성과 활동 단건 조회."""
    row = db.get(PerformanceRecord, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Activity record not found")
    return _row_to_dict(row)
