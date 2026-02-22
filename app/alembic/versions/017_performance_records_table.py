"""performance_records 통합 테이블 (회의록·보고서·이메일 성과 활동)

Revision ID: 017_performance_records
Revises: 016_meetings_table
Create Date: 2026-02-22

- 한 row = 한 직원의 한 분기·한 텍스트 유형 1건.
- 실적/활동 분기 단위 조회, AI 성장 분석용 텍스트 저장.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "017_performance_records"
down_revision: Union[str, None] = "016_meetings_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "performance_records",
        sa.Column("id", sa.String(64), primary_key=True, comment="레코드 ID (예: PF0001)"),
        sa.Column("employee_id", sa.String(64), nullable=False, index=True, comment="직원 ID (HP001, NP001 등)"),
        sa.Column("period", sa.String(32), nullable=False, index=True, comment="분기 (예: 2025-Q1)"),
        sa.Column("text_type", sa.String(32), nullable=False, index=True, comment="meeting|report|email"),
        sa.Column("content", sa.Text(), nullable=False, comment="본문 텍스트"),
        sa.Column("tags", JSONB(), nullable=True, comment="태그 배열"),
        sa.Column("grade", sa.String(32), nullable=True, index=True, comment="high|normal"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
    )
    op.create_index(
        "ix_performance_records_employee_period",
        "performance_records",
        ["employee_id", "period"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_performance_records_employee_period", table_name="performance_records")
    op.drop_table("performance_records")
