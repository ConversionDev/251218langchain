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
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from application.shared.audit_service import write_audit_log  # type: ignore
from application.employee.employee_service import EmployeeService  # type: ignore
from core.database import get_db  # type: ignore

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
    search: Optional[str] = None,
) -> List[Dict[str, Any]] | PaginatedEmployeesResponse:
    """직원 목록. page/pageSize가 있으면 페이징 응답, 없으면 전체 목록. search: 이름·부서·ID 검색."""
    svc = EmployeeService(db)
    if page is not None or pageSize is not None:
        items, total = svc.list_paginated(page or 1, pageSize or 20, employment_type=employmentType, search=search)
        p = max(1, page or 1)
        ps = max(1, min(100, pageSize or 20))
        return PaginatedEmployeesResponse(items=items, total=total, page=p, pageSize=ps)
    return svc.list_all()


@router.get("/next-id", response_model=Dict[str, Any])
def get_next_employee_id(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """다음 직원 ID 제안 (직원 추가 폼용)."""
    return {"nextId": EmployeeService(db).get_next_id()}


@router.get("/check-resume-hash", response_model=Dict[str, Any])
def check_resume_hash(
    resume_hash: str = "",
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """이력서 파일 해시로 이미 등록된 지원인지 확인. 중복 제출 방지용."""
    existing = EmployeeService(db).find_by_resume_hash(resume_hash)
    if existing:
        return {"exists": True, "existing": existing}
    return {"exists": False}


@router.get("/{employee_id}", response_model=Dict[str, Any])
def get_employee(employee_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원 단건 조회."""
    one = EmployeeService(db).get(employee_id)
    if not one:
        raise HTTPException(status_code=404, detail="Employee not found")
    return one


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_employee(
    payload: EmployeePayload,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any] | JSONResponse:
    """직원 생성. 동일 이력서(resumeFileHash)가 이미 있으면 409."""
    try:
        svc = EmployeeService(db)
        created = svc.create(payload.model_dump(exclude_unset=False))
        write_audit_log(
            db, request=request, entity_type="employee", action="create",
            entity_id=created.get("id") or payload.id,
            after_data=created, reason="create employee",
        )
        return created
    except ValueError as e:
        if str(e) == "ALREADY_EXISTS":
            existing = svc.find_by_resume_hash(payload.resumeFileHash or "")
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
    svc = EmployeeService(db)
    data = payload.model_dump(exclude_unset=True)
    data["id"] = employee_id
    before = svc.get(employee_id)
    result = svc.update(employee_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    write_audit_log(
        db, request=request, entity_type="employee", action="update", entity_id=employee_id,
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
    svc = EmployeeService(db)
    before = svc.get(employee_id)
    if not svc.delete(employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    write_audit_log(
        db, request=request, entity_type="employee", action="delete", entity_id=employee_id,
        before_data=before, after_data=None, reason="delete employee",
    )


# 서브라우터 include (prefix 없음 — 이 router의 /employees 아래로 마운트됨)
from api.rest.employee_embedding_router import router as _embedding_router  # noqa: E402
from api.rest.employee_analysis_router import router as _analysis_router  # noqa: E402

router.include_router(_embedding_router)
router.include_router(_analysis_router)
