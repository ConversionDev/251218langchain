"""alembic_version.version_num 길이 확장 (실무: 긴 revision ID 대응).

Revision ID: 025_alembic_version_widen
Revises: 024_mail_external_id_received
Create Date: 2026-02-26

- alembic_version.version_num을 VARCHAR(128)로 확장.
- 기본값이 VARCHAR(32)라 긴 revision ID 시 StringDataRightTruncation 발생 방지.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "025_alembic_version_widen"
down_revision: Union[str, None] = "024_mail_external_id_received"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")


def downgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32)")
