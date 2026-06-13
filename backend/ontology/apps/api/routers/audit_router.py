"""감사 로그 조회 API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from core.database import get_db  # type: ignore
from infrastructure.persistence.repositories.audit_log_repository import list_logs as repo_list_logs  # type: ignore

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


class AuditLogListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int


def _parse_dt(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception:
        return None


@router.get("/logs", response_model=AuditLogListResponse)
def get_audit_logs(
    entityType: Optional[str] = Query(None, description="엔터티 타입"),
    entityId: Optional[str] = Query(None, description="엔터티 ID"),
    action: Optional[str] = Query(None, description="액션"),
    actor: Optional[str] = Query(None, description="수행자"),
    fromAt: Optional[str] = Query(None, description="시작 시각 ISO"),
    toAt: Optional[str] = Query(None, description="종료 시각 ISO"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    items = repo_list_logs(
        db,
        entity_type=entityType,
        entity_id=entityId,
        action=action,
        actor=actor,
        from_dt=_parse_dt(fromAt),
        to_dt=_parse_dt(toAt),
        limit=limit,
    )
    return AuditLogListResponse(items=items, total=len(items))
