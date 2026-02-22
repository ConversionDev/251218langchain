"""meetings 테이블 생성 (회의록 성과 관리)

Revision ID: 016_meetings_table
Revises: 015_rejection_reason
Create Date: 2026-02-20

- 회의록 저장: 제목, 일시, 참석자, 내용, AI 분석 결과.
- participants JSONB로 employee_id 연결, 사원별 필터링 가능.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "016_meetings_table"
down_revision: Union[str, None] = "015_rejection_reason"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="회의록 ID"),
        sa.Column("title", sa.String(512), nullable=False, comment="회의 제목"),
        sa.Column("meeting_date", sa.DateTime(timezone=True), nullable=False, comment="회의 일시 (UTC)"),
        sa.Column("location", sa.String(256), nullable=True, comment="회의 장소 또는 온라인 링크"),
        sa.Column("participants", JSONB(), nullable=True, comment="참석자 목록 [{employeeId, name, role}]"),
        sa.Column("content", sa.Text(), nullable=True, comment="회의 내용 원문"),
        sa.Column("summary", sa.Text(), nullable=True, comment="AI 생성 요약"),
        sa.Column("competency_keywords", JSONB(), nullable=True, comment="AI 추출 역량 키워드"),
        sa.Column("competency_analysis", JSONB(), nullable=True, comment="AI 역량 분석 결과"),
        sa.Column("analysis_status", sa.String(32), nullable=True, comment="분석 상태: pending|completed|failed"),
        sa.Column("created_by", sa.String(256), nullable=True, comment="등록자"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="수정 시각"),
    )
    # 참석자 검색용 GIN 인덱스
    op.create_index("ix_meetings_participants", "meetings", ["participants"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_meetings_participants", table_name="meetings")
    op.drop_table("meetings")
