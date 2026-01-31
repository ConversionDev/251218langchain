"""
Player 모델
선수 정보를 관리하는 SQLAlchemy 모델입니다.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String

from core.database import Base  # type: ignore


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
