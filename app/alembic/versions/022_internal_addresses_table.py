"""internal_addresses 테이블 (사내 주소록: 공용함·그룹).

Revision ID: 022_internal_addresses
Revises: 021_drop_soccer
Create Date: 2026-02-26

- 사내 주소록 확장: 직원(employees) 외 공용 메일함·메일 그룹 저장.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "022_internal_addresses"
down_revision: Union[str, None] = "021_drop_soccer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "internal_addresses",
        sa.Column("id", sa.String(64), primary_key=True, comment="주소 ID"),
        sa.Column("type", sa.String(16), nullable=False, index=True, comment="shared | group"),
        sa.Column("display_name", sa.String(256), nullable=False, comment="표시명"),
        sa.Column("email", sa.String(512), nullable=False, comment="메일 주소"),
        sa.Column("department", sa.String(128), nullable=True, comment="부서/용도"),
        sa.Column("metadata", JSONB(), nullable=True, comment="멤버 ID 목록 등 (group용)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
    )


def downgrade() -> None:
    op.drop_table("internal_addresses")
