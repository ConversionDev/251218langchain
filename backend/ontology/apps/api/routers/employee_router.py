"""직원 CRUD API — Neon employees 테이블.

GET    /api/employees            목록 (페이징 옵션)
GET    /api/employees/next-id    다음 ID 제안
GET    /api/employees/check-resume-hash  이력서 중복 확인
GET    /api/employees/{id}       단건 조회
POST   /api/employees            생성
PUT    /api/employees/{id}       수정
DELETE /api/employees/{id}       삭제

임베딩 갱신  → employee_embedding_router (POST /embedding, /profile-backfill)
AI 분석      → employee_analysis_router  (POST /{id}/analyze)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from api.routers._employee_shared import _write_audit_log  # type: ignore
from core.database import get_db  # type: ignore
from domain.hub.repositories.employee_repository import (  # type: ignore
    create as repo_create,
    delete as repo_delete,
    find_by_resume_hash as repo_find_by_resume_hash,
    get_by_id as repo_get_by_id,
    get_next_id as repo_get_next_id,
    list_all as repo_list_all,
    list_paginated as repo_list_paginated,
    update as repo_update,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["Employees"])


class EmployeePayload(BaseModel):
    """직원 생성/수정 요청 (프론트 Employee 호환 camelCase)."""

    id: str = Field(..., description="직원 ID")
    name: str = Field("", description="이름")
    jobTitle: str = Field("", description="직급")
    department: str = Field("", description="부서")
    email: str | None = None
    applicationDate: str | None = Field(None, description="지원일 YYYY-MM-DD")
    joinedAt: str | None = Field(None, description="입사일 YYYY-MM-DD")
    successDna: Dict[str, Any] | None = None
    disclosureMetrics: Dict[str, Any] | None = None
    gender: str | None = None
    age: int | None = None
    employmentType: str | None = None
    trainingHours: int | None = None
    resume: Dict[str, Any] | None = None
    resumeText: str | None = Field(None, description="이력서 원본 추출 텍스트")
    resumeFileHash: str | None = Field(None, description="이력서 파일 SHA-256")
    matchedDepartment: str | None = None
    status: str | None = Field(None, description="채용 상태: pending|screening|hired|rejected")
    successDnaReason: str | None = Field(None, description="평가 근거")
    rejectionReason: str | None = Field(None, description="탈락 사유")

    model_config = {"extra": "allow"}


class PaginatedEmployeesResponse(BaseModel):
    """페이징된 직원 목록 응답."""

    items: List[Dict[str, Any]]
    total: int
    page: int
    pageSize: int


@router.get("", response_model=None)
def list_employees(
    db: Session = Depends(get_db),
    page: Optional[int] = None,
    pageSize: Optional[int] = None,
    employmentType: Optional[str] = None,
) -> List[Dict[str, Any]] | PaginatedEmployeesResponse:
    """직원 목록. page/pageSize가 있으면 페이징 응답, 없으면 전체 목록."""
    if page is not None or pageSize is not None:
        p = max(1, page or 1)
        ps = max(1, min(100, pageSize or 20))
        items, total = repo_list_paginated(db, page=p, page_size=ps, employment_type=employmentType)
        return PaginatedEmployeesResponse(items=items, total=total, page=p, pageSize=ps)
    return repo_list_all(db)


@router.get("/next-id", response_model=Dict[str, Any])
def get_next_employee_id(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """다음 직원 ID 제안 (직원 추가 폼용)."""
    return {"nextId": repo_get_next_id(db)}


@router.get("/check-resume-hash", response_model=Dict[str, Any])
def check_resume_hash(
    resume_hash: str = "",
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """이력서 파일 해시로 이미 등록된 지원인지 확인. 중복 제출 방지용."""
    h = (resume_hash or "").strip()
    if not h:
        return {"exists": False}
    existing = repo_find_by_resume_hash(db, h)
    if existing:
        return {"exists": True, "existing": existing}
    return {"exists": False}


@router.get("/{employee_id}", response_model=Dict[str, Any])
def get_employee(employee_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원 단건 조회."""
    one = repo_get_by_id(db, employee_id)
    if not one:
        raise HTTPException(status_code=404, detail="Employee not found")
    return one


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_employee(
    payload: EmployeePayload,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any] | JSONResponse:
    """직원 생성. 동일 이력서(resumeFileHash)가 이미 있으면 409.
    - 신입(new_hire): 지원일을 서버 시각(UTC)으로, 입사일은 비워 둠.
    """
    try:
        data = payload.model_dump(exclude_unset=False)
        if data.get("employmentType") == "new_hire":
            data["applicationDate"] = datetime.now(timezone.utc)
            data["joinedAt"] = None
            data["status"] = "pending"
            data["successDna"] = None
            data["successDnaReason"] = None
        created = repo_create(db, data)
        _write_audit_log(
            db, request=request, action="create",
            entity_id=created.get("id") or payload.id,
            after_data=created, reason="create employee",
        )
        return created
    except ValueError as e:
        if str(e) == "ALREADY_EXISTS":
            resume_hash = (payload.resumeFileHash or "").strip()
            existing = repo_find_by_resume_hash(db, resume_hash) if resume_hash else None
            return JSONResponse(
                status_code=409,
                content={"detail": "동일한 이력서가 이미 등록되어 있습니다", "existing": existing or {}},
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("직원 생성 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail="지원서 저장 중 오류가 발생했습니다. DB 연결과 서버 로그를 확인해 주세요.",
        )


@router.put("/{employee_id}", response_model=Dict[str, Any])
def update_employee(
    employee_id: str,
    payload: EmployeePayload,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """직원 수정. id는 path 기준."""
    data = payload.model_dump(exclude_unset=True)
    data["id"] = employee_id
    before = repo_get_by_id(db, employee_id)
    result = repo_update(db, employee_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    _write_audit_log(
        db, request=request, action="update", entity_id=employee_id,
        before_data=before, after_data=result, reason="update employee",
    )
    return result


@router.delete("/{employee_id}", status_code=204)
def delete_employee(
    employee_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """직원 삭제."""
    before = repo_get_by_id(db, employee_id)
    if not repo_delete(db, employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    _write_audit_log(
        db, request=request, action="delete", entity_id=employee_id,
        before_data=before, after_data=None, reason="delete employee",
    )


# 서브라우터 include (prefix 없음 — 이 router의 /employees 아래로 마운트됨)
from api.routers.employee_embedding_router import router as _embedding_router  # noqa: E402
from api.routers.employee_analysis_router import router as _analysis_router  # noqa: E402

router.include_router(_embedding_router)
router.include_router(_analysis_router)
