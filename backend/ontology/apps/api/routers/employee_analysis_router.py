"""직원 AI 분석 API.

POST /employees/{id}/analyze: resume + 성과활동 → Success DNA 분석
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from application.shared.audit_service import write_audit_log  # type: ignore
from application.employee.employee_service import EmployeeService  # type: ignore
from core.database import get_db  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Employees"])


@router.post("/{employee_id}/analyze", response_model=Dict[str, Any])
async def analyze_employee_resume(
    employee_id: str,
    request: Request,
    db: Session = Depends(get_db),
    force: bool = Query(
        False,
        description="true면 Success DNA가 있어도 LLM 재분석. false면 신입만 기존 DNA 유지하고 LLM 생략 가능",
    ),
) -> Dict[str, Any]:
    """직원 AI 분석.
    - 신입(new_hire): resume 중심 분석 후 status → screening
    - 기존 직원(regular): resume + 성과활동(performance_records) 기반 분석
    - 신입이고 DB에 Success DNA가 이미 있으면 force=false일 때 LLM 호출 생략
    """
    svc = EmployeeService(db)
    before = svc.get(employee_id)
    try:
        out = await svc.analyze(employee_id, force=force)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail="Employee not found")
        raise HTTPException(status_code=422, detail=msg)
    except Exception as e:
        logger.exception("AI 분석 실패 employee_id=%s: %s", employee_id, e)
        raise HTTPException(status_code=500, detail=f"AI 분석 중 오류: {e}")

    skipped = out.get("analysisSkipped", False)
    if skipped:
        reason = (
            "ai analyze skipped (existing successDna); status→screening"
            if (before or {}).get("status") == "pending"
            else "ai analyze skipped (existing successDna)"
        )
    else:
        reason = "ai analyze"
    write_audit_log(
        db, request=request, entity_type="employee", action="analyze", entity_id=employee_id,
        before_data=before, after_data=out, reason=reason,
    )
    return out
