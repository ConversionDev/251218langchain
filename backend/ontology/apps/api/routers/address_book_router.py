"""
사내 주소록 API — 직원(employees) + 공용함·그룹(internal_addresses) 통합 조회 및 공용·그룹 CRUD.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from application.address_book.address_book_service import AddressBookService  # type: ignore
from core.database import get_db  # type: ignore

router = APIRouter(prefix="/address-book", tags=["Address Book (사내 주소록)"])


class CreateAddressBody(BaseModel):
    """공용·그룹 생성 요청."""
    type: str = Field(..., description="shared | group")
    displayName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    department: Optional[str] = None
    ownerEmployeeId: Optional[str] = Field(None, description="대표 소유자(직원 ID), 수신 메일 매핑용")
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class UpdateAddressBody(BaseModel):
    """공용·그룹 수정 요청."""
    displayName: Optional[str] = Field(None, min_length=1)
    email: Optional[str] = Field(None, min_length=1)
    department: Optional[str] = None
    ownerEmployeeId: Optional[str] = Field(None, description="대표 소유자(직원 ID)")
    metadata: Optional[Dict[str, Any]] = None


def _normalize_q(q: Optional[str]) -> str:
    return (q or "").strip().lower()


@router.get("", response_model=List[Dict[str, Any]])
def get_address_book(
    q: Optional[str] = Query(None, description="검색: 이름·이메일·부서"),
    type: Optional[str] = Query(None, description="person | shared | group"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """직원 + 공용함·그룹을 한 목록으로 반환. 메일 받는 사람 선택용. 모두 DB(employees / internal_addresses) 기준."""
    return AddressBookService(db).list_all(type_filter=type, search=_normalize_q(q) or None)


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_address(
    body: CreateAddressBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """공용 메일함 또는 그룹 1건 생성. id 없으면 자동 생성."""
    if body.type not in ("shared", "group"):
        raise HTTPException(status_code=400, detail="type must be shared or group")
    try:
        return AddressBookService(db).create(
            type=body.type,
            display_name=body.displayName,
            email=body.email,
            department=body.department,
            owner_employee_id=body.ownerEmployeeId,
            metadata_=body.metadata,
            id=body.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{address_id}", response_model=Dict[str, Any])
def update_address(
    address_id: str,
    body: UpdateAddressBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """공용·그룹 1건 수정. internal_addresses에 있는 id만 가능."""
    result = AddressBookService(db).update(
        address_id,
        display_name=body.displayName,
        email=body.email,
        department=body.department,
        owner_employee_id=body.ownerEmployeeId,
        metadata_=body.metadata,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Address not found or not editable (employees are managed elsewhere)")
    return result


@router.delete("/{address_id}", status_code=204)
def delete_address(
    address_id: str,
    db: Session = Depends(get_db),
) -> None:
    """공용·그룹 1건 삭제. internal_addresses에 있는 id만 가능."""
    if not AddressBookService(db).delete(address_id):
        raise HTTPException(status_code=404, detail="Address not found or not deletable")
