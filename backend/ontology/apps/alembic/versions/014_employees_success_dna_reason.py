"""employees 테이블에 success_dna_reason 컬럼 추가 (AI 평가 근거)

Revision ID: 014_success_dna_reason
Revises: 013_employees_status
Create Date: 2026-02-19

- ATS 관리자용: Success DNA 점수를 어떤 이유로 매겼는지 LLM이 생성한 요약 텍스트.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014_success_dna_reason"
down_revision: Union[str, None] = "013_employees_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "success_dna_reason",
            sa.Text(),
            nullable=True,
            comment="AI 평가 근거 (Success DNA 점수 산정 이유, 관리자 화면 표시용)",
        ),
    )


def downgrade() -> None:
    op.drop_column("employees", "success_dna_reason")
