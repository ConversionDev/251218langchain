"""employees에 hired_at 추가 (ATS 합격 시각, 입사 확정 후에도 유지).

Revision ID: 028_employees_hired_at
Revises: cd00d8e8cfc0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "028_employees_hired_at"
down_revision: Union[str, None] = "cd00d8e8cfc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "hired_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="ATS 합격(status=hired) 최초 처리 시각. 입사 확정 후에도 유지",
        ),
    )
    op.execute(
        """
        UPDATE employees
        SET hired_at = COALESCE(updated_at, created_at, NOW())
        WHERE LOWER(TRIM(COALESCE(status, ''))) = 'hired'
          AND hired_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("employees", "hired_at")
