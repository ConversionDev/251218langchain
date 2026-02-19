"""employees 테이블에서 age_band 컬럼 제거

Revision ID: 011_drop_age_band
Revises: 010_application_date
Create Date: 2026-02-19

- 연령대는 age(만 나이)로 파생. age_band 컬럼 제거.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011_drop_age_band"
down_revision: Union[str, None] = "010_application_date"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("employees", "age_band")


def downgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("age_band", sa.String(32), nullable=True, comment="연령대"),
    )
