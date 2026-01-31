"""Squashed V10 domain initial migration

Revision ID: squashed_v10
Revises:
Create Date: 2026-01-29

stadiums, teams (순환 FK), players, schedules 테이블만 관리.
ExaOne 임베딩 테이블(*_embeddings)은 별도 마이그레이션 add_exaone_embedding_tables에서 생성.

사용법:
- 새 환경: alembic upgrade head (또는 python -m alembic upgrade head)
- 이미 테이블이 있는 DB: python -m alembic stamp squashed_v10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "squashed_v10"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # stadiums (FK 없이 먼저 생성)
    op.create_table(
        "stadiums",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="경기장 ID"),
        sa.Column("stadium_code", sa.String(length=10), nullable=False, comment="경기장 코드"),
        sa.Column("statdium_name", sa.String(length=100), nullable=False, comment="경기장 이름"),
        sa.Column("hometeam_id", sa.BigInteger(), nullable=True, comment="홈팀 ID (FK -> teams.id)"),
        sa.Column("hometeam_code", sa.String(length=10), nullable=True, comment="홈팀 코드"),
        sa.Column("seat_count", sa.Integer(), nullable=True, comment="좌석 수"),
        sa.Column("address", sa.Text(), nullable=True, comment="주소"),
        sa.Column("ddd", sa.String(length=10), nullable=True, comment="지역번호"),
        sa.Column("tel", sa.String(length=20), nullable=True, comment="전화번호"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stadium_code"),
    )

    # teams (FK 없이 먼저 생성)
    op.create_table(
        "teams",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="팀 ID"),
        sa.Column("stadium_id", sa.BigInteger(), nullable=True, comment="경기장 ID (FK -> stadiums.id)"),
        sa.Column("team_code", sa.String(length=10), nullable=False, comment="팀 코드"),
        sa.Column("region_name", sa.String(length=50), nullable=True, comment="지역명"),
        sa.Column("team_name", sa.String(length=100), nullable=False, comment="팀 이름"),
        sa.Column("e_team_name", sa.String(length=100), nullable=True, comment="팀 영문 이름"),
        sa.Column("orig_yyyy", sa.String(length=4), nullable=True, comment="창단 연도"),
        sa.Column("zip_code1", sa.String(length=10), nullable=True, comment="우편번호 앞자리"),
        sa.Column("zip_code2", sa.String(length=10), nullable=True, comment="우편번호 뒷자리"),
        sa.Column("address", sa.Text(), nullable=True, comment="주소"),
        sa.Column("ddd", sa.String(length=10), nullable=True, comment="지역번호"),
        sa.Column("tel", sa.String(length=20), nullable=True, comment="전화번호"),
        sa.Column("fax", sa.String(length=20), nullable=True, comment="팩스번호"),
        sa.Column("homepage", sa.Text(), nullable=True, comment="홈페이지"),
        sa.Column("owner", sa.String(length=100), nullable=True, comment="구단주"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_code"),
    )

    # 순환 참조 FK 추가
    op.execute(
        "ALTER TABLE stadiums ADD CONSTRAINT stadiums_hometeam_id_fkey "
        "FOREIGN KEY (hometeam_id) REFERENCES teams(id)"
    )
    op.execute(
        "ALTER TABLE teams ADD CONSTRAINT teams_stadium_id_fkey "
        "FOREIGN KEY (stadium_id) REFERENCES stadiums(id)"
    )

    # players
    op.create_table(
        "players",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="선수 ID"),
        sa.Column("team_id", sa.BigInteger(), nullable=False, comment="팀 ID (FK -> teams.id)"),
        sa.Column("player_name", sa.String(length=100), nullable=False, comment="선수 이름"),
        sa.Column("e_player_name", sa.String(length=100), nullable=True, comment="선수 영문 이름"),
        sa.Column("nickname", sa.String(length=100), nullable=True, comment="별명"),
        sa.Column("join_yyyy", sa.String(length=4), nullable=True, comment="입단 연도"),
        sa.Column("position", sa.String(length=10), nullable=True, comment="포지션 (GK, DF, MF, FW)"),
        sa.Column("back_no", sa.Integer(), nullable=True, comment="등번호"),
        sa.Column("nation", sa.String(length=50), nullable=True, comment="국적"),
        sa.Column("birth_date", sa.String(length=10), nullable=True, comment="생년월일 (YYYY-MM-DD)"),
        sa.Column("solar", sa.String(length=1), nullable=True, comment="양력/음력 구분 (1: 양력, 2: 음력)"),
        sa.Column("height", sa.Integer(), nullable=True, comment="키 (cm)"),
        sa.Column("weight", sa.Integer(), nullable=True, comment="몸무게 (kg)"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # schedules
    op.create_table(
        "schedules",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="경기 ID"),
        sa.Column("stadium_id", sa.BigInteger(), nullable=False, comment="경기장 ID (FK -> stadiums.id)"),
        sa.Column("hometeam_id", sa.BigInteger(), nullable=False, comment="홈팀 ID (FK -> teams.id)"),
        sa.Column("awayteam_id", sa.BigInteger(), nullable=False, comment="원정팀 ID (FK -> teams.id)"),
        sa.Column("stadium_code", sa.String(length=10), nullable=False, comment="경기장 코드"),
        sa.Column("sche_date", sa.String(length=8), nullable=False, comment="경기 일자 (YYYYMMDD)"),
        sa.Column("gubun", sa.String(length=1), nullable=False, comment="경기 구분 (Y/N)"),
        sa.Column("hometeam_code", sa.String(length=10), nullable=False, comment="홈팀 코드"),
        sa.Column("awayteam_code", sa.String(length=10), nullable=False, comment="원정팀 코드"),
        sa.Column("home_score", sa.Integer(), nullable=True, comment="홈팀 점수"),
        sa.Column("away_score", sa.Integer(), nullable=True, comment="원정팀 점수"),
        sa.ForeignKeyConstraint(["awayteam_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["hometeam_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["stadium_id"], ["stadiums.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("schedules")
    op.drop_table("players")
    op.execute("ALTER TABLE stadiums DROP CONSTRAINT IF EXISTS stadiums_hometeam_id_fkey")
    op.execute("ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_stadium_id_fkey")
    op.drop_table("teams")
    op.drop_table("stadiums")
