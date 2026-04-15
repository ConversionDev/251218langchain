"""employees 테이블 (직원·이력서·Success DNA·RAG 임베딩)

Revision ID: 007_employees
Revises: 006_competency_anchors
Create Date: 2026-02-17

- Core 직원 등록/수정/삭제 및 직무 처리(부서 매칭 등)용.
- RAG: embedding_content(임베딩용 텍스트), embedding vector(1024) BGE-m3, HNSW 인덱스.
  직원 검색은 Neon pgvector(HNSW)만 사용(FAISS 미사용). LangGraph RAG 노드에서 인물 질문 시 검색.
- B-tree: department, name, job_title, (department, name) — 필터·목록 조회 가속.
- disclosure_metrics: 다중 공시 표준. docs/disclosure-metrics-design.md 참고.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "007_employees"
down_revision: Union[str, None] = "006_competency_anchors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1024  # BGE-m3 dense 출력 차원과 일치
HNSW_M = 24
HNSW_EF_CONSTRUCTION = 128


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.String(64), nullable=False, comment="직원 ID (예: E001)"),
        sa.Column("name", sa.String(256), nullable=False, comment="이름"),
        sa.Column("job_title", sa.String(256), nullable=False, server_default="", comment="직급"),
        sa.Column("department", sa.String(256), nullable=False, server_default="", comment="부서"),
        sa.Column("email", sa.String(512), nullable=True, comment="이메일"),
        sa.Column("joined_at", sa.String(32), nullable=True, comment="입사일 YYYY-MM-DD"),
        sa.Column("success_dna", JSONB(), nullable=True, comment="Success DNA 5대 역량"),
        sa.Column("behavioral_dna", JSONB(), nullable=True, comment="비정형 분석 기반 역량"),
        sa.Column("behavioral_source", sa.Text(), nullable=True, comment="behavioralDna 출처 요약"),
        sa.Column("behavioral_source_items", JSONB(), nullable=True, comment="회의록/이메일 등 원문 목록"),
        sa.Column(
            "disclosure_metrics",
            JSONB(),
            nullable=True,
            comment="공시 지표(다중 표준). IFRS/ISO 30414 등. 레거시 flat 또는 items[].",
        ),
        sa.Column("gender", sa.String(32), nullable=True, comment="성별 ISO 30414"),
        sa.Column("age_band", sa.String(32), nullable=True, comment="연령대"),
        sa.Column("employment_type", sa.String(32), nullable=True, comment="고용 형태"),
        sa.Column("training_hours", sa.Integer(), nullable=True, comment="연간 교육훈련 시간"),
        sa.Column("resume", JSONB(), nullable=True, comment="이력서 학력·경력·스킬·자격증"),
        sa.Column("matched_department", sa.String(256), nullable=True, comment="추천 부서"),
        sa.Column("embedding_content", sa.Text(), nullable=True, comment="RAG 임베딩용 텍스트(역량 페르소나 등)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="생성 시각"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="수정 시각"),
        sa.PrimaryKeyConstraint("id"),
    )
    # B-tree: 필터·목록 조회 가속 (005/006과 동일하게 USING btree 명시)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employees_department "
        "ON employees USING btree (department)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employees_name "
        "ON employees USING btree (name)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employees_job_title "
        "ON employees USING btree (job_title)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_employees_department_name "
        "ON employees USING btree (department, name)"
    )
    op.execute("ALTER TABLE employees ADD COLUMN embedding vector(1024)")
    op.execute("COMMENT ON COLUMN employees.embedding IS 'BGE-m3 1024차원, RAG 검색용'")
    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_employees_embedding_hnsw
        ON employees USING hnsw (embedding vector_cosine_ops)
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION})
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_employees_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_employees_department_name")
    op.execute("DROP INDEX IF EXISTS idx_employees_job_title")
    op.execute("DROP INDEX IF EXISTS idx_employees_name")
    op.execute("DROP INDEX IF EXISTS idx_employees_department")
    op.drop_table("employees")
