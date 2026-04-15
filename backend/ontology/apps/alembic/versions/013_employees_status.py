"""employees 테이블에 status 컬럼 추가 (ATS 채용 상태)

Revision ID: 013_employees_status
Revises: 012_app_date_datetime
Create Date: 2026-02-19

- pending: 미검토, screening: 심사 중, hired: 합격, rejected: 탈락
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013_employees_status"
down_revision: Union[str, None] = "012_app_date_datetime"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "status",
            sa.String(32),
            nullable=True,
            comment="채용 상태: pending(미검토)|screening(심사 중)|hired(합격)|rejected(탈락)",
        ),
    )


def downgrade() -> None:
    op.drop_column("employees", "status")
