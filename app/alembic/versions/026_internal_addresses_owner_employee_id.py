"""internal_addresses에 owner_employee_id 추가 (공용/그룹 대표 소유자).

Revision ID: 026_internal_addr_owner
Revises: 025_alembic_version_widen
Create Date: 2026-02-26

- 수신 메일 Resolver: 공용/그룹 메일함의 소유자(직원 ID) 지정용.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "026_internal_addr_owner"
down_revision: Union[str, None] = "025_alembic_version_widen"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "internal_addresses",
        sa.Column("owner_employee_id", sa.String(64), nullable=True, comment="대표 소유자(직원 ID), 수신 메일 매핑용"),
    )


def downgrade() -> None:
    op.drop_column("internal_addresses", "owner_employee_id")
