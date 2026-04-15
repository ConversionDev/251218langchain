"""disclosures 테이블에 standard_type, section_title, metadata, unique_id 추가

Revision ID: 003_disclosure_meta
Revises: 002_disclosure
Create Date: 2026-02-07

- standard_type: ISO30414, IFRS_S1, IFRS_S2, OECD 등
- section_title: 조항/섹션 제목 (검색 정확도·출처 표기)
- metadata: JSON (페이지, 발행 연도 등)
- unique_id: 재적재/업서트용 고유 키 (source + section_id + chunk_index)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "003_disclosure_meta"
down_revision: Union[str, None] = "002_disclosure"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("disclosures", sa.Column("standard_type", sa.Text(), nullable=True, comment="ISO30414, IFRS_S1 등"))
    op.add_column("disclosures", sa.Column("section_title", sa.Text(), nullable=True, comment="조항/섹션 제목"))
    op.add_column("disclosures", sa.Column("metadata", JSONB(), nullable=True, comment="페이지·발행연도 등 추가 정보"))
    op.add_column("disclosures", sa.Column("unique_id", sa.Text(), nullable=True, comment="재적재/업서트용 고유 키"))


def downgrade() -> None:
    op.drop_column("disclosures", "unique_id")
    op.drop_column("disclosures", "metadata")
    op.drop_column("disclosures", "section_title")
    op.drop_column("disclosures", "standard_type")
