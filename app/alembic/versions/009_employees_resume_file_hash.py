"""employees 테이블에 resume_file_hash 컬럼 추가

Revision ID: 009_resume_hash
Revises: 008_employees_age
Create Date: 2026-02-17

- 동일 이력서 파일(SHA-256) 중복 등록 방지용.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009_resume_hash"
down_revision: Union[str, None] = "008_employees_age"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("resume_file_hash", sa.String(64), nullable=True, comment="이력서 파일 SHA-256, 동일 이력서 중복 방지"),
    )
    op.create_index("ix_employees_resume_file_hash", "employees", ["resume_file_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_employees_resume_file_hash", table_name="employees")
    op.drop_column("employees", "resume_file_hash")
