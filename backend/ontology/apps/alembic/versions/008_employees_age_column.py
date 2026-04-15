"""employees 테이블에 age(연령) 컬럼 추가

Revision ID: 008_employees_age
Revises: 007_employees
Create Date: 2026-02-17

- 연령대(age_band) 대신 정확한 연령(만 나이) 저장용.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008_employees_age"
down_revision: Union[str, None] = "007_employees"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("age", sa.Integer(), nullable=True, comment="연령(만 나이)"),
    )


def downgrade() -> None:
    op.drop_column("employees", "age")
