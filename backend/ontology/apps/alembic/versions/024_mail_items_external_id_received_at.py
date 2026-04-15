"""mail_items에 external_id(UNIQUE), received_at 추가 (수신 메일 전략 1단계).

Revision ID: 024_mail_external_id_received (32자 이하: alembic_version.version_num 제한)
Revises: 023_mail_items
Create Date: 2026-02-26

- 수신 중복 방지: external_id (Message-ID) UNIQUE
- 수신 시각: received_at (받은편지함 정렬·표시)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "024_mail_external_id_received"
down_revision: Union[str, None] = "023_mail_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mail_items",
        sa.Column("external_id", sa.String(512), nullable=True, comment="Message-ID, 수신 중복 방지"),
    )
    op.add_column(
        "mail_items",
        sa.Column("received_at", sa.DateTime(), nullable=True, comment="수신 시각 (받은 메일용)"),
    )
    op.create_index("ix_mail_items_external_id", "mail_items", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_mail_items_external_id", table_name="mail_items")
    op.drop_column("mail_items", "received_at")
    op.drop_column("mail_items", "external_id")
