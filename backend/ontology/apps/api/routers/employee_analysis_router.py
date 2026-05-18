"""직원 AI 분석 API.

POST /employees/{id}/analyze: resume + 성과활동 → Success DNA 분석
"""

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from api.routers._employee_shared import _write_audit_log  # type: ignore
from api.services.resume_analyzer import _resume_dict_to_text, analyze_resume_text  # type: ignore
from core.database import get_db  # type: ignore
from domain.hub.repositories.employee_repository import (  # type: ignore
    get_by_id as repo_get_by_id,
    update as repo_update,
)
from domain.hub.repositories.performance_record_repository import (  # type: ignore
    list_by_employee as repo_list_performance_by_employee,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Employees"])

_DNA_KEYS = ("leadership", "technical", "creativity", "collaboration", "adaptability")


def _row_has_success_dna(one: Dict[str, Any]) -> bool:
    """5대 역량이 모두 숫자로 있으면 DB에 분석 결과가 있다고 본다."""
    d = one.get("successDna")
    if not isinstance(d, dict):
        return False
    for k in _DNA_KEYS:
        v = d.get(k)
        if v is None:
            return False
        try:
            float(v)
        except (TypeError, ValueError):
            return False
    return True


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
    one = repo_get_by_id(db, employee_id)
    if not one:
        raise HTTPException(status_code=404, detail="Employee not found")

    is_new_hire = (one.get("employmentType") or "").strip().lower() == "new_hire"
    if is_new_hire and _row_has_success_dna(one) and not force:
        st = str(one.get("status") or "").strip().lower()
        if st == "pending":
            updated = repo_update(db, employee_id, {"status": "screening"})
            out = dict(updated or one)
            out["analysisSkipped"] = True
            _write_audit_log(
                db, request=request, action="analyze", entity_id=employee_id,
                before_data=one, after_data=updated or one,
                reason="ai analyze skipped (existing successDna); status→screening",
            )
            return out
        out = dict(one)
        out["analysisSkipped"] = True
        _write_audit_log(
            db, request=request, action="analyze", entity_id=employee_id,
            before_data=one, after_data=one,
            reason="ai analyze skipped (existing successDna)",
        )
        return out

    # 이력서 텍스트 — 원본 추출 텍스트 우선, 없으면 구조화 데이터로 대체
    stored_resume_text = (one.get("resumeText") or "").strip()
    resume = one.get("resume")
    resume_text = stored_resume_text if stored_resume_text else (
        _resume_dict_to_text(resume) if isinstance(resume, dict) else ""
    )

    # 성과 활동 텍스트 (기존 직원 보완)
    perf_rows = repo_list_performance_by_employee(db, employee_id, limit=50)
    perf_lines: List[str] = []
    for r in perf_rows:
        period = str(r.get("period") or "").strip()
        text_type = str(r.get("textType") or "").strip()
        content = str(r.get("content") or "").strip()
        if content:
            perf_lines.append(f"[{period}][{text_type}] {content}")
    perf_text = "\n".join(perf_lines)

    text_parts = []
    if resume_text and len(resume_text.strip()) >= 10:
        text_parts.append("## 이력/프로필\n" + resume_text.strip())
    if perf_text and len(perf_text.strip()) >= 10:
        text_parts.append("## 성과활동\n" + perf_text.strip())
    text = "\n\n".join(text_parts)
    if not text or len(text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="분석 가능한 텍스트가 없습니다. (resume 또는 성과활동 기록 필요)",
        )

    try:
        result = await asyncio.to_thread(analyze_resume_text, text, True)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("AI 분석 실패 employee_id=%s: %s", employee_id, e)
        raise HTTPException(status_code=500, detail=f"AI 분석 중 오류: {e}")

    payload: Dict[str, Any] = {
        "successDna": result.get("successDna"),
        "successDnaReason": result.get("successDnaReason"),
    }
    if (one.get("employmentType") or "").strip().lower() == "new_hire":
        payload["status"] = "screening"

    updated = repo_update(db, employee_id, payload)
    _write_audit_log(
        db, request=request, action="analyze", entity_id=employee_id,
        before_data=one, after_data=updated or one, reason="ai analyze",
    )
    out = dict(updated or one)
    out["analysisSkipped"] = False
    return out
