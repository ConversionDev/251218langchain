"""application_date를 제출일시(시분초) 저장용 DateTime(TIMESTAMPTZ)로 변경

Revision ID: 012_app_date_datetime
Revises: 011_drop_age_band
Create Date: 2026-02-19

- 지원서 제출 순간의 시각을 저장하기 위해 날짜+시분초 저장.
- 기존 YYYY-MM-DD 문자열은 해당일 00:00:00 UTC로 변환.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012_app_date_datetime"
down_revision: Union[str, None] = "011_drop_age_band"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # VARCHAR(32) → TIMESTAMP WITH TIME ZONE. 기존 'YYYY-MM-DD'는 해당일 00:00:00 UTC로 해석
    op.alter_column(
        "employees",
        "application_date",
        existing_type=sa.String(32),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="(application_date::timestamp without time zone) AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    # TIMESTAMPTZ → VARCHAR(32), 날짜만 YYYY-MM-DD로 저장
    op.alter_column(
        "employees",
        "application_date",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.String(32),
        existing_nullable=True,
        postgresql_using="to_char(application_date AT TIME ZONE 'UTC', 'YYYY-MM-DD')",
    )
