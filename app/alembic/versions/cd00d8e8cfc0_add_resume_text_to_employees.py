"""add_resume_text_to_employees

Revision ID: cd00d8e8cfc0
Revises: 027_mail_ai_status
Create Date: 2026-04-07 22:44:17.600038

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'cd00d8e8cfc0'
down_revision: Union[str, None] = '027_mail_ai_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'employees',
        sa.Column(
            'resume_text',
            sa.Text(),
            nullable=True,
            comment='이력서 원본 추출 텍스트 (ATS AI 분석용 원문 보존)',
        ),
    )


def downgrade() -> None:
    op.drop_column('employees', 'resume_text')
