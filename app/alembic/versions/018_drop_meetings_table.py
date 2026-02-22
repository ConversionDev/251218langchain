"""Drop meetings table (통합 테이블 performance_records로 대체).

Revision ID: 018_drop_meetings_table
Revises: 017_performance_records
Create Date: 2026-02-19 12:00:00.000000
"""

from alembic import op

revision = "018_drop_meetings_table"
down_revision = "017_performance_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop meetings table (회의록·보고서·이메일을 performance_records로 통합)."""
    op.drop_table("meetings")


def downgrade() -> None:
    """Recreate meetings table if needed (rollback용)."""
    op.execute("""
        CREATE TABLE meetings (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            meeting_date TIMESTAMP,
            location TEXT,
            participants JSONB DEFAULT '[]',
            content TEXT,
            summary TEXT,
            competency_keywords JSONB DEFAULT '[]',
            competency_analysis JSONB DEFAULT '{}',
            analysis_status VARCHAR(20) DEFAULT 'pending',
            created_by TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ix_meetings_meeting_date ON meetings (meeting_date)")
    op.execute("CREATE INDEX ix_meetings_analysis_status ON meetings (analysis_status)")
