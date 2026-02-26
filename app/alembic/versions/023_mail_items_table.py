"""mail_items 테이블 (받은/보낸/임시보관/휴지통 공통).

Revision ID: 023_mail_items
Revises: 022_internal_addresses
Create Date: 2026-02-26

- 메일 공통 설계: 한 테이블로 폴더별 관리.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "023_mail_items"
down_revision: Union[str, None] = "022_internal_addresses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mail_items",
        sa.Column("id", sa.String(64), primary_key=True, comment="메일 ID"),
        sa.Column("folder", sa.String(16), nullable=False, index=True, comment="inbox | sent | draft | trash"),
        sa.Column("owner_employee_id", sa.String(64), nullable=False, index=True, comment="메일함 소유자(직원 ID)"),
        sa.Column("from_employee_id", sa.String(64), nullable=True, comment="발신 직원 ID"),
        sa.Column("from_display", sa.String(256), nullable=False, server_default="", comment="발신자 표시명"),
        sa.Column("from_email", sa.String(512), nullable=True, comment="발신자 이메일"),
        sa.Column("to_address_id", sa.String(64), nullable=True, comment="수신자 주소록 ID"),
        sa.Column("to_display", sa.String(256), nullable=True, comment="수신자 표시명"),
        sa.Column("to_email", sa.String(512), nullable=True, comment="수신자 이메일"),
        sa.Column("subject", sa.String(512), nullable=False, server_default="", comment="제목"),
        sa.Column("body", sa.Text(), nullable=True, comment="본문"),
        sa.Column("sent_at", sa.DateTime(), nullable=True, comment="발송 시각 (draft는 null)"),
        sa.Column("is_starred", sa.Boolean(), nullable=False, server_default=sa.false(), comment="중요 메일"),
        sa.Column("is_unread", sa.Boolean(), nullable=False, server_default=sa.true(), comment="읽지 않음"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="수정 시각"),
    )


def downgrade() -> None:
    op.drop_table("mail_items")
