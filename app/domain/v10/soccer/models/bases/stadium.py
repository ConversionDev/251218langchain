"""
Stadium 모델
경기장 정보를 관리하는 SQLAlchemy 모델입니다.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text

from core.database import Base  # type: ignore


class Stadium(Base):  # type: ignore[misc]
    """경기장 모델.

    Attributes:
        id: 경기장 ID (BigInt)
        stadium_code: 경기장 코드 (고유)
        statdium_name: 경기장 이름 (원본 데이터의 오타 유지)
        hometeam_id: 홈팀 ID (FK -> teams.id, 선택)
        hometeam_code: 홈팀 코드
        seat_count: 좌석 수
        address: 주소
        ddd: 지역번호
        tel: 전화번호
    """

    __tablename__ = "stadiums"

    id = Column(BigInteger, primary_key=True, comment="경기장 ID")
    stadium_code = Column(String(10), unique=True, nullable=False, comment="경기장 코드")
    statdium_name = Column(String(100), nullable=False, comment="경기장 이름")
    hometeam_id = Column(
        BigInteger,
        ForeignKey("teams.id"),
        nullable=True,
        comment="홈팀 ID (FK -> teams.id)",
    )
    hometeam_code = Column(String(10), nullable=True, comment="홈팀 코드")
    seat_count = Column(Integer, nullable=True, comment="좌석 수")
    address = Column(Text, nullable=True, comment="주소")
    ddd = Column(String(10), nullable=True, comment="지역번호")
    tel = Column(String(20), nullable=True, comment="전화번호")

    def __repr__(self) -> str:
        """문자열 표현."""
        return (
            f"<Stadium(id={self.id}, stadium_name='{self.statdium_name}', "
            f"stadium_code='{self.stadium_code}')>"
        )

    def to_dict(self) -> dict:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "stadium_code": self.stadium_code,
            "statdium_name": self.statdium_name,
            "hometeam_id": self.hometeam_id,
            "hometeam_code": self.hometeam_code,
            "seat_count": self.seat_count,
            "address": self.address,
            "ddd": self.ddd,
            "tel": self.tel,
        }
