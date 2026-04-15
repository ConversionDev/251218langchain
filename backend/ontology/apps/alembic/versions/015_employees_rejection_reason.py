"""employees 테이블에 rejection_reason 컬럼 추가 (탈락 사유)

Revision ID: 015_rejection_reason
Revises: 014_success_dna_reason
Create Date: 2026-02-19

- ATS: 탈락 처리 시 관리자가 입력하는 탈락 사유. 이의 제기·감사 대응용.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "015_rejection_reason"
down_revision: Union[str, None] = "014_success_dna_reason"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "rejection_reason",
            sa.Text(),
            nullable=True,
            comment="탈락 사유 (ATS 관리자 입력, 이의 제기·감사 대응용)",
        ),
    )


def downgrade() -> None:
    op.drop_column("employees", "rejection_reason")
