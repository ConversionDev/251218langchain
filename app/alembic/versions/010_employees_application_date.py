"""employees 테이블에 application_date 컬럼 추가

Revision ID: 010_application_date
Revises: 009_resume_hash
Create Date: 2026-02-19

- 지원일(지원서 제출일)과 입사일(joined_at) 분리.
- 지원 시점에는 application_date만 저장, joined_at은 입사 확정 후 설정.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010_application_date"
down_revision: Union[str, None] = "009_resume_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "application_date",
            sa.String(32),
            nullable=True,
            comment="지원일 YYYY-MM-DD (입사지원서 제출일)",
        ),
    )


def downgrade() -> None:
    op.drop_column("employees", "application_date")
