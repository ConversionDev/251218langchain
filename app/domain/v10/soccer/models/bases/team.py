"""
Team 모델
팀 정보를 관리하는 SQLAlchemy 모델입니다.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, String, Text

from core.database import Base  # type: ignore


class Team(Base):  # type: ignore[misc]
    """팀 모델.

    Attributes:
        id: 팀 ID (BigInt)
        stadium_id: 경기장 ID (FK -> stadiums.id)
        team_code: 팀 코드 (고유)
        region_name: 지역명
        team_name: 팀 이름
        e_team_name: 팀 영문 이름
        orig_yyyy: 창단 연도
        zip_code1: 우편번호 앞자리
        zip_code2: 우편번호 뒷자리
        address: 주소
        ddd: 지역번호
        tel: 전화번호
        fax: 팩스번호
        homepage: 홈페이지
        owner: 구단주
    """

    __tablename__ = "teams"

    id = Column(BigInteger, primary_key=True, comment="팀 ID")
    stadium_id = Column(
        BigInteger,
        ForeignKey("stadiums.id"),
        nullable=True,
        comment="경기장 ID (FK -> stadiums.id)",
    )
    team_code = Column(String(10), unique=True, nullable=False, comment="팀 코드")
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

    def __repr__(self) -> str:
        """문자열 표현."""
        return f"<Team(id={self.id}, team_name='{self.team_name}', team_code='{self.team_code}')>"

    def to_dict(self) -> dict:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "stadium_id": self.stadium_id,
            "team_code": self.team_code,
            "region_name": self.region_name,
            "team_name": self.team_name,
            "e_team_name": self.e_team_name,
            "orig_yyyy": self.orig_yyyy,
            "zip_code1": self.zip_code1,
            "zip_code2": self.zip_code2,
            "address": self.address,
            "ddd": self.ddd,
            "tel": self.tel,
            "fax": self.fax,
            "homepage": self.homepage,
            "owner": self.owner,
        }
