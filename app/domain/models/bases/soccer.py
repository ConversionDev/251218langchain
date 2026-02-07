"""
Soccer 도메인 ORM — players, teams, stadiums, schedules (통일: 이 모듈 하나만 사용).

가이드: 베이스 테이블에 embedding, embedding_content 컬럼 포함 (단일 테이블).
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text

from core.database import Base  # type: ignore

from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore

VECTOR_DIM = BGE_M3_DENSE_DIM


class Player(Base):  # type: ignore[misc]
    """선수 모델.

    Attributes:
        id: 선수 ID (BigInt)
        team_id: 팀 ID (FK -> teams.id)
        player_name: 선수 이름
        e_player_name: 선수 영문 이름
        nickname: 별명
        join_yyyy: 입단 연도
        position: 포지션 (GK, DF, MF, FW)
        back_no: 등번호
        nation: 국적
        birth_date: 생년월일 (YYYY-MM-DD)
        solar: 양력/음력 구분 (1: 양력, 2: 음력)
        height: 키 (cm)
        weight: 몸무게 (kg)
    """

    __tablename__ = "players"

    id = Column(BigInteger, primary_key=True, comment="선수 ID")
    team_id = Column(
        BigInteger,
        ForeignKey("teams.id"),
        nullable=False,
        comment="팀 ID (FK -> teams.id)",
    )
    player_name = Column(String(100), nullable=False, comment="선수 이름")
    e_player_name = Column(String(100), nullable=True, comment="선수 영문 이름")
    nickname = Column(String(100), nullable=True, comment="별명")
    join_yyyy = Column(String(4), nullable=True, comment="입단 연도")
    position = Column(String(10), nullable=True, comment="포지션 (GK, DF, MF, FW)")
    back_no = Column(Integer, nullable=True, comment="등번호")
    nation = Column(String(50), nullable=True, comment="국적")
    birth_date = Column(String(10), nullable=True, comment="생년월일 (YYYY-MM-DD)")
    solar = Column(String(1), nullable=True, comment="양력/음력 구분 (1: 양력, 2: 음력)")
    height = Column(Integer, nullable=True, comment="키 (cm)")
    weight = Column(Integer, nullable=True, comment="몸무게 (kg)")
    embedding_content = Column(Text, nullable=True, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)")  # type: ignore[var-annotated]

    def __repr__(self) -> str:
        """문자열 표현."""
        return f"<Player(id={self.id}, player_name='{self.player_name}', team_id={self.team_id})>"

    def to_dict(self) -> dict:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "team_id": self.team_id,
            "player_name": self.player_name,
            "e_player_name": self.e_player_name,
            "nickname": self.nickname,
            "join_yyyy": self.join_yyyy,
            "position": self.position,
            "back_no": self.back_no,
            "nation": self.nation,
            "birth_date": self.birth_date,
            "solar": self.solar,
            "height": self.height,
            "weight": self.weight,
        }


class Stadium(Base):  # type: ignore[misc]
    """경기장. __tablename__ = stadiums (DB 컬럼 statdium_name 유지)."""
    __tablename__ = "stadiums"
    id = Column(BigInteger, primary_key=True, comment="경기장 ID")
    stadium_code = Column(String(10), nullable=False, unique=True, comment="경기장 코드")
    statdium_name = Column(String(100), nullable=False, comment="경기장 이름")
    hometeam_id = Column(BigInteger, nullable=True, comment="홈팀 ID")
    hometeam_code = Column(String(10), nullable=True, comment="홈팀 코드")
    seat_count = Column(Integer, nullable=True, comment="좌석 수")
    address = Column(Text, nullable=True, comment="주소")
    ddd = Column(String(10), nullable=True, comment="지역번호")
    tel = Column(String(20), nullable=True, comment="전화번호")
    embedding_content = Column(Text, nullable=True, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)")  # type: ignore[var-annotated]


class Team(Base):  # type: ignore[misc]
    """팀. __tablename__ = teams."""
    __tablename__ = "teams"
    id = Column(BigInteger, primary_key=True, comment="팀 ID")
    stadium_id = Column(BigInteger, nullable=True, comment="경기장 ID")
    team_code = Column(String(10), nullable=False, unique=True, comment="팀 코드")
    region_name = Column(String(50), nullable=True, comment="지역명")
    team_name = Column(String(100), nullable=False, comment="팀 이름")
    e_team_name = Column(String(100), nullable=True, comment="팀 영문 이름")
    orig_yyyy = Column(String(4), nullable=True, comment="창단 연도")
    zip_code1 = Column(String(10), nullable=True, comment="우편번호 앞자리")
    zip_code2 = Column(String(10), nullable=True, comment="우편번호 뒷자리")
    address = Column(Text, nullable=True, comment="주소")
    ddd = Column(String(10), nullable=True, comment="지역번호")
    tel = Column(String(20), nullable=True, comment="전화번호")
    fax = Column(String(20), nullable=True, comment="팩스번호")
    homepage = Column(Text, nullable=True, comment="홈페이지")
    owner = Column(String(100), nullable=True, comment="구단주")
    embedding_content = Column(Text, nullable=True, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)")  # type: ignore[var-annotated]


class Schedule(Base):  # type: ignore[misc]
    """경기 일정. __tablename__ = schedules."""
    __tablename__ = "schedules"
    id = Column(BigInteger, primary_key=True, comment="경기 ID")
    stadium_id = Column(BigInteger, ForeignKey("stadiums.id"), nullable=False, comment="경기장 ID")
    hometeam_id = Column(BigInteger, ForeignKey("teams.id"), nullable=False, comment="홈팀 ID")
    awayteam_id = Column(BigInteger, ForeignKey("teams.id"), nullable=False, comment="원정팀 ID")
    stadium_code = Column(String(10), nullable=False, comment="경기장 코드")
    sche_date = Column(String(8), nullable=False, comment="경기 일자 (YYYYMMDD)")
    gubun = Column(String(1), nullable=False, comment="경기 구분 (Y/N)")
    hometeam_code = Column(String(10), nullable=False, comment="홈팀 코드")
    awayteam_code = Column(String(10), nullable=False, comment="원정팀 코드")
    home_score = Column(Integer, nullable=True, comment="홈팀 점수")
    away_score = Column(Integer, nullable=True, comment="원정팀 점수")
    embedding_content = Column(Text, nullable=True, comment="임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(VECTOR_DIM), nullable=True, comment="벡터 임베딩 (BGE-m3 1024)")  # type: ignore[var-annotated]
