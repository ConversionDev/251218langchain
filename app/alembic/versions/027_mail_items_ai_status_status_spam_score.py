"""mail_items에 ai_status, status, spam_score, processed_at, retry_count, last_failed_at, ai_result_raw 추가.

Revision ID: 027_mail_ai_status
Revises: 026_internal_addr_owner
Create Date: 2026-03-02

- ai_status: AI 처리 상태 (PENDING|PROCESSING|SUCCESS|FAILED), DEFAULT 'PENDING'
- status: 수신 도메인 상태 (RECEIVED|REJECTED)
- spam_score, processed_at, retry_count, last_failed_at, ai_result_raw (운영/장애 대응)
- 복합 인덱스 (ai_status, processed_at) 로 워커 쿼리 최적화
- external_id UNIQUE는 024에서 이미 적용됨 (전제)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "027_mail_ai_status"
down_revision: Union[str, None] = "026_internal_addr_owner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mail_items",
        sa.Column(
            "ai_status",
            sa.String(16),
            nullable=True,
            server_default="PENDING",
            comment="AI 처리 상태: PENDING|PROCESSING|SUCCESS|FAILED",
        ),
    )
    op.add_column(
        "mail_items",
        sa.Column(
            "status",
            sa.String(16),
            nullable=True,
            comment="수신 도메인 상태: RECEIVED|REJECTED",
        ),
    )
    op.add_column(
        "mail_items",
        sa.Column("spam_score", sa.Float(), nullable=True, comment="LLaMA 스팸 점수 (0~1)"),
    )
    op.add_column(
        "mail_items",
        sa.Column(
            "processed_at",
            sa.DateTime(),
            nullable=True,
            comment="워커 처리 완료 시각 (인덱스·SLA용)",
        ),
    )
    op.add_column(
        "mail_items",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="AI 실패 재시도 횟수",
        ),
    )
    op.add_column(
        "mail_items",
        sa.Column(
            "last_failed_at",
            sa.DateTime(),
            nullable=True,
            comment="마지막 AI 실패 시각",
        ),
    )
    op.add_column(
        "mail_items",
        sa.Column(
            "ai_result_raw",
            sa.Text(),
            nullable=True,
            comment="실패 시 에러 메시지 또는 AI 원시 응답 (디버깅용)",
        ),
    )
    # 워커 쿼리: WHERE ai_status = 'PENDING' 최적화
    op.create_index(
        "ix_mail_items_ai_status_processed_at",
        "mail_items",
        ["ai_status", "processed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_mail_items_ai_status_processed_at", table_name="mail_items")
    op.drop_column("mail_items", "ai_result_raw")
    op.drop_column("mail_items", "last_failed_at")
    op.drop_column("mail_items", "retry_count")
    op.drop_column("mail_items", "processed_at")
    op.drop_column("mail_items", "spam_score")
    op.drop_column("mail_items", "status")
    op.drop_column("mail_items", "ai_status")
