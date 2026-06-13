"""
수신 메일 To 주소 → 메일함 소유자(owner_employee_id) Resolver.

전략: To가 직원/공용/그룹 주소록에 없으면 None 반환 → 수신 API에서 4xx·저장 안 함.
"""

from typing import Optional

from sqlalchemy import func  # type: ignore[import-untyped]
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from infrastructure.persistence.models.employee_orm import Employee  # type: ignore
from infrastructure.persistence.models.internal_address_orm import InternalAddress  # type: ignore


def _normalize_email(email: Optional[str]) -> str:
    """비교용 이메일 정규화 (strip, lower)."""
    if not email or not isinstance(email, str):
        return ""
    return email.strip().lower()


def resolve_owner_by_to_email(db: Session, to_email: str) -> Optional[str]:
    """
    수신 메일의 To 주소로 메일함 소유자(직원 ID)를 반환한다.

    - employees에서 email 일치(대소문자 무시) → 해당 직원 id 반환
    - 없으면 internal_addresses에서 email 일치 → owner_employee_id 반환 (None이면 그대로 None)
    - 둘 다 없거나 공용/그룹에 owner_employee_id가 없으면 None (매핑 실패 → 저장 차단)

    Returns:
        owner_employee_id 또는 None
    """
    key = _normalize_email(to_email)
    if not key:
        return None

    # 1) 직원 이메일
    emp = (
        db.query(Employee)
        .filter(Employee.email.isnot(None), func.lower(Employee.email) == key)
        .first()
    )
    if emp:
        return emp.id

    # 2) 공용/그룹 주소록
    addr = (
        db.query(InternalAddress)
        .filter(func.lower(InternalAddress.email) == key)
        .first()
    )
    if addr and addr.owner_employee_id:
        return addr.owner_employee_id.strip() or None

    return None
