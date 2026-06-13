"""주소록 유스케이스 — 직원 + 공용함·그룹 통합 조회 및 CRUD."""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from infrastructure.persistence.repositories.employee_repository import list_all as employee_list_all  # type: ignore
from infrastructure.persistence.repositories.internal_address_repository import (  # type: ignore
    create as internal_address_create,
    delete_by_id as internal_address_delete,
    list_all as internal_address_list_all,
    update as internal_address_update,
)


class AddressBookService:

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(
        self,
        type_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """직원 + 공용함·그룹 통합 목록. type_filter: person | shared | group."""
        items: List[Dict[str, Any]] = []

        if type_filter is None or type_filter == "person":
            for e in employee_list_all(self.db):
                items.append({
                    "id": e.get("id"),
                    "type": "person",
                    "displayName": e.get("name") or "",
                    "email": e.get("email") or "",
                    "department": e.get("department") or "",
                    "source": "employees",
                })

        if type_filter is None or type_filter in ("shared", "group"):
            addr_type = type_filter if type_filter in ("shared", "group") else None
            for a in internal_address_list_all(self.db, type_filter=addr_type):
                items.append({
                    "id": a.get("id"),
                    "type": a.get("type") or "shared",
                    "displayName": a.get("displayName") or "",
                    "email": a.get("email") or "",
                    "department": a.get("department") or "",
                    "source": "internal_addresses",
                })

        if search:
            q = search.strip().lower()
            items = [
                i for i in items
                if q in (i.get("displayName") or "").lower()
                or q in (i.get("email") or "").lower()
                or q in (i.get("department") or "").lower()
                or q in (i.get("id") or "").lower()
            ]

        return items[:500]

    def create(
        self,
        type: str,
        display_name: str,
        email: str,
        department: Optional[str] = None,
        owner_employee_id: Optional[str] = None,
        metadata_: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """공용·그룹 1건 생성. id 없으면 자동 생성. Raises ValueError on duplicate."""
        return internal_address_create(
            self.db,
            type=type,
            display_name=display_name,
            email=email,
            department=department,
            owner_employee_id=owner_employee_id,
            metadata_=metadata_,
            id=id,
        )

    def update(
        self,
        address_id: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        owner_employee_id: Optional[str] = None,
        metadata_: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """공용·그룹 1건 수정. 없으면 None."""
        return internal_address_update(
            self.db,
            id=address_id,
            display_name=display_name,
            email=email,
            department=department,
            owner_employee_id=owner_employee_id,
            metadata_=metadata_,
        )

    def delete(self, address_id: str) -> bool:
        """공용·그룹 1건 삭제. 없으면 False."""
        return internal_address_delete(self.db, address_id)
