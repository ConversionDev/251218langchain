"""통합 초기 마이그레이션 (Soccer 단일 테이블 + embedding 컬럼, pgvector 가이드)

Revision ID: 001_initial
Revises:
Create Date: 2026-02-07

Soccer 도메인: stadiums, teams, players, schedules
각 베이스 테이블에 embedding vector(1024), embedding_content text 컬럼 포함 (가이드: 단일 테이블).

사용법:
- 새 환경: alembic upgrade head
- 이미 테이블이 있는 DB: alembic stamp 001_initial
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
except ImportError:
    Vector = None

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1024


def upgrade() -> None:
    # 1) pgvector 확장
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2) stadiums (FK 없이 먼저 생성) + embedding 컬럼
    cols_stadiums = [
        sa.Column("id", sa.BigInteger(), nullable=False, comment="경기장 ID"),
        sa.Column("stadium_code", sa.String(length=10), nullable=False, comment="경기장 코드"),
        sa.Column("statdium_name", sa.String(length=100), nullable=False, comment="경기장 이름"),
        sa.Column("hometeam_id", sa.BigInteger(), nullable=True, comment="홈팀 ID (FK -> teams.id)"),
        sa.Column("hometeam_code", sa.String(length=10), nullable=True, comment="홈팀 코드"),
        sa.Column("seat_count", sa.Integer(), nullable=True, comment="좌석 수"),
        sa.Column("address", sa.Text(), nullable=True, comment="주소"),
        sa.Column("ddd", sa.String(length=10), nullable=True, comment="지역번호"),
        sa.Column("tel", sa.String(length=20), nullable=True, comment="전화번호"),
    ]
    if Vector is not None:
        cols_stadiums.append(sa.Column("embedding_content", sa.Text(), nullable=True, comment="임베딩용 텍스트"))
        cols_stadiums.append(sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)"))
    op.create_table(
        "stadiums",
        *cols_stadiums,
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stadium_code"),
    )
    if Vector is None:
        op.execute("ALTER TABLE stadiums ADD COLUMN embedding_content TEXT")
        op.execute("ALTER TABLE stadiums ADD COLUMN embedding vector(1024)")

    # 3) teams + embedding 컬럼
    cols_teams = [
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
    ]
    if Vector is not None:
        cols_teams.append(sa.Column("embedding_content", sa.Text(), nullable=True, comment="임베딩용 텍스트"))
        cols_teams.append(sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)"))
    op.create_table(
        "teams",
        *cols_teams,
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_code"),
    )
    if Vector is None:
        op.execute("ALTER TABLE teams ADD COLUMN embedding_content TEXT")
        op.execute("ALTER TABLE teams ADD COLUMN embedding vector(1024)")

    # 4) 순환 참조 FK
    op.execute(
        "ALTER TABLE stadiums ADD CONSTRAINT stadiums_hometeam_id_fkey "
        "FOREIGN KEY (hometeam_id) REFERENCES teams(id)"
    )
    op.execute(
        "ALTER TABLE teams ADD CONSTRAINT teams_stadium_id_fkey "
        "FOREIGN KEY (stadium_id) REFERENCES stadiums(id)"
    )

    # 5) players + embedding 컬럼
    cols_players = [
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
    ]
    if Vector is not None:
        cols_players.append(sa.Column("embedding_content", sa.Text(), nullable=True, comment="임베딩용 텍스트"))
        cols_players.append(sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)"))
    op.create_table(
        "players",
        *cols_players,
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    if Vector is None:
        op.execute("ALTER TABLE players ADD COLUMN embedding_content TEXT")
        op.execute("ALTER TABLE players ADD COLUMN embedding vector(1024)")

    # 6) schedules + embedding 컬럼
    cols_schedules = [
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
    ]
    if Vector is not None:
        cols_schedules.append(sa.Column("embedding_content", sa.Text(), nullable=True, comment="임베딩용 텍스트"))
        cols_schedules.append(sa.Column("embedding", Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)"))
    op.create_table(
        "schedules",
        *cols_schedules,
        sa.ForeignKeyConstraint(["awayteam_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["hometeam_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["stadium_id"], ["stadiums.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    if Vector is None:
        op.execute("ALTER TABLE schedules ADD COLUMN embedding_content TEXT")
        op.execute("ALTER TABLE schedules ADD COLUMN embedding vector(1024)")


def downgrade() -> None:
    op.drop_table("schedules")
    op.drop_table("players")
    op.execute("ALTER TABLE stadiums DROP CONSTRAINT IF EXISTS stadiums_hometeam_id_fkey")
    op.execute("ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_stadium_id_fkey")
    op.drop_table("teams")
    op.drop_table("stadiums")
