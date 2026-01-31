"""
Schedule 모델
경기 일정 정보를 관리하는 SQLAlchemy 모델입니다.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String

from core.database import Base  # type: ignore


class Schedule(Base):  # type: ignore[misc]
    """경기 일정 모델.

    Attributes:
        id: 경기 ID (BigInt)
        stadium_id: 경기장 ID (FK -> stadiums.id)
        hometeam_id: 홈팀 ID (FK -> teams.id)
        awayteam_id: 원정팀 ID (FK -> teams.id)
        stadium_code: 경기장 코드
        sche_date: 경기 일자 (YYYYMMDD)
        gubun: 경기 구분 (Y: 정규리그, N: 컵대회 등)
        hometeam_code: 홈팀 코드
        awayteam_code: 원정팀 코드
        home_score: 홈팀 점수
        away_score: 원정팀 점수
    """

    __tablename__ = "schedules"

    id = Column(BigInteger, primary_key=True, comment="경기 ID")
    stadium_id = Column(
        BigInteger,
        ForeignKey("stadiums.id"),
        nullable=False,
        comment="경기장 ID (FK -> stadiums.id)",
    )
    hometeam_id = Column(
        BigInteger,
        ForeignKey("teams.id"),
        nullable=False,
        comment="홈팀 ID (FK -> teams.id)",
    )
    awayteam_id = Column(
        BigInteger,
        ForeignKey("teams.id"),
        nullable=False,
        comment="원정팀 ID (FK -> teams.id)",
    )
    stadium_code = Column(String(10), nullable=False, comment="경기장 코드")
    sche_date = Column(String(8), nullable=False, comment="경기 일자 (YYYYMMDD)")
    gubun = Column(String(1), nullable=False, comment="경기 구분 (Y/N)")
    hometeam_code = Column(String(10), nullable=False, comment="홈팀 코드")
    awayteam_code = Column(String(10), nullable=False, comment="원정팀 코드")
    home_score = Column(Integer, nullable=True, comment="홈팀 점수")
    away_score = Column(Integer, nullable=True, comment="원정팀 점수")

    def __repr__(self) -> str:
        """문자열 표현."""
        return (
            f"<Schedule(id={self.id}, sche_date='{self.sche_date}', "
            f"hometeam_id={self.hometeam_id}, awayteam_id={self.awayteam_id})>"
        )

    def to_dict(self) -> dict:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "stadium_id": self.stadium_id,
            "hometeam_id": self.hometeam_id,
            "awayteam_id": self.awayteam_id,
            "stadium_code": self.stadium_code,
            "sche_date": self.sche_date,
            "gubun": self.gubun,
            "hometeam_code": self.hometeam_code,
            "awayteam_code": self.awayteam_code,
            "home_score": self.home_score,
            "away_score": self.away_score,
        }
