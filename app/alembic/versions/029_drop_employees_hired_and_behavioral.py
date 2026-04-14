"""employees에서 hired_at 및 행동(behavioral_*) 컬럼 제거.

Revision ID: 029_drop_employees_hired_and_behavioral
Revises: 028_employees_hired_at
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "029_drop_employees_hired_and_behavioral"
down_revision: Union[str, None] = "028_employees_hired_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("employees", "hired_at")
    op.drop_column("employees", "behavioral_source_items")
    op.drop_column("employees", "behavioral_source")
    op.drop_column("employees", "behavioral_dna")


def downgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("behavioral_dna", JSONB(), nullable=True, comment="비정형 분석 기반 역량"),
    )
    op.add_column(
        "employees",
        sa.Column("behavioral_source", sa.Text(), nullable=True, comment="behavioralDna 출처 요약"),
    )
    op.add_column(
        "employees",
        sa.Column("behavioral_source_items", JSONB(), nullable=True, comment="회의록/이메일 등 원문 목록"),
    )
    op.add_column(
        "employees",
        sa.Column(
            "hired_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="ATS 합격(status=hired) 최초 처리 시각. 입사 확정 후에도 유지",
        ),
    )
