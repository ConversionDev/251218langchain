"""
Soccer 도메인 Pydantic 전송 모델.

domain.models.bases.soccer (Player, Team, Stadium, Schedule ORM)을 참조한
API 요청/응답·직렬화용 DTO. from_attributes=True 로 ORM 인스턴스 → DTO 변환.
"""

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------


class PlayerModel(BaseModel):
    """선수 응답/직렬화 모델. SQLAlchemy Player ORM 대응."""

    id: Optional[int] = Field(None, description="선수 ID")
    team_id: Optional[int] = Field(None, description="팀 ID")
    player_name: Optional[str] = Field(None, description="선수 이름", max_length=100)
    e_player_name: Optional[str] = Field(None, description="선수 영문 이름", max_length=100)
    nickname: Optional[str] = Field(None, description="별명", max_length=100)
    join_yyyy: Optional[str] = Field(None, description="입단 연도", max_length=4)
    position: Optional[str] = Field(None, description="포지션 (GK, DF, MF, FW)", max_length=10)
    back_no: Optional[int] = Field(None, description="등번호")
    nation: Optional[str] = Field(None, description="국적", max_length=50)
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)", max_length=10)
    solar: Optional[str] = Field(None, description="양력/음력 구분 (1: 양력, 2: 음력)", max_length=1)
    height: Optional[int] = Field(None, description="키 (cm)")
    weight: Optional[int] = Field(None, description="몸무게 (kg)")

    model_config = {"from_attributes": True}


class PlayerCreateModel(BaseModel):
    """선수 생성 요청 모델."""

    team_id: Optional[int] = Field(None, description="팀 ID")
    player_name: Optional[str] = Field(None, description="선수 이름", max_length=100)
    e_player_name: Optional[str] = Field(None, description="선수 영문 이름", max_length=100)
    nickname: Optional[str] = Field(None, description="별명", max_length=100)
    join_yyyy: Optional[str] = Field(None, description="입단 연도", max_length=4)
    position: Optional[str] = Field(None, description="포지션", max_length=10)
    back_no: Optional[int] = Field(None, description="등번호")
    nation: Optional[str] = Field(None, description="국적", max_length=50)
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)", max_length=10)
    solar: Optional[str] = Field(None, description="양력/음력 구분", max_length=1)
    height: Optional[int] = Field(None, description="키 (cm)")
    weight: Optional[int] = Field(None, description="몸무게 (kg)")


class PlayerUpdateModel(BaseModel):
    """선수 수정 요청 모델."""

    team_id: Optional[int] = Field(None, description="팀 ID")
    player_name: Optional[str] = Field(None, description="선수 이름", max_length=100)
    e_player_name: Optional[str] = Field(None, description="선수 영문 이름", max_length=100)
    nickname: Optional[str] = Field(None, description="별명", max_length=100)
    join_yyyy: Optional[str] = Field(None, description="입단 연도", max_length=4)
    position: Optional[str] = Field(None, description="포지션", max_length=10)
    back_no: Optional[int] = Field(None, description="등번호")
    nation: Optional[str] = Field(None, description="국적", max_length=50)
    birth_date: Optional[str] = Field(None, description="생년월일", max_length=10)
    solar: Optional[str] = Field(None, description="양력/음력 구분", max_length=1)
    height: Optional[int] = Field(None, description="키 (cm)")
    weight: Optional[int] = Field(None, description="몸무게 (kg)")


# ---------------------------------------------------------------------------
# Stadium (ORM 컬럼명 statdium_name 유지)
# ---------------------------------------------------------------------------


class StadiumModel(BaseModel):
    """경기장 응답/직렬화 모델. SQLAlchemy Stadium ORM 대응."""

    id: Optional[int] = Field(None, description="경기장 ID")
    stadium_code: Optional[str] = Field(None, description="경기장 코드", max_length=10)
    statdium_name: Optional[str] = Field(None, description="경기장 이름", max_length=100)
    hometeam_id: Optional[int] = Field(None, description="홈팀 ID")
    hometeam_code: Optional[str] = Field(None, description="홈팀 코드", max_length=10)
    seat_count: Optional[int] = Field(None, description="좌석 수")
    address: Optional[str] = Field(None, description="주소")
    ddd: Optional[str] = Field(None, description="지역번호", max_length=10)
    tel: Optional[str] = Field(None, description="전화번호", max_length=20)

    model_config = {"from_attributes": True}


class StadiumCreateModel(BaseModel):
    """경기장 생성 요청 모델."""

    stadium_code: Optional[str] = Field(None, description="경기장 코드", max_length=10)
    statdium_name: Optional[str] = Field(None, description="경기장 이름", max_length=100)
    hometeam_id: Optional[int] = Field(None, description="홈팀 ID")
    hometeam_code: Optional[str] = Field(None, description="홈팀 코드", max_length=10)
    seat_count: Optional[int] = Field(None, description="좌석 수")
    address: Optional[str] = Field(None, description="주소")
    ddd: Optional[str] = Field(None, description="지역번호", max_length=10)
    tel: Optional[str] = Field(None, description="전화번호", max_length=20)


class StadiumUpdateModel(BaseModel):
    """경기장 수정 요청 모델."""

    stadium_code: Optional[str] = Field(None, description="경기장 코드", max_length=10)
    statdium_name: Optional[str] = Field(None, description="경기장 이름", max_length=100)
    hometeam_id: Optional[int] = Field(None, description="홈팀 ID")
    hometeam_code: Optional[str] = Field(None, description="홈팀 코드", max_length=10)
    seat_count: Optional[int] = Field(None, description="좌석 수")
    address: Optional[str] = Field(None, description="주소")
    ddd: Optional[str] = Field(None, description="지역번호", max_length=10)
    tel: Optional[str] = Field(None, description="전화번호", max_length=20)


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------


class TeamModel(BaseModel):
    """팀 응답/직렬화 모델. SQLAlchemy Team ORM 대응."""

    id: Optional[int] = Field(None, description="팀 ID")
    stadium_id: Optional[int] = Field(None, description="경기장 ID")
    team_code: Optional[str] = Field(None, description="팀 코드", max_length=10)
    region_name: Optional[str] = Field(None, description="지역명", max_length=50)
    team_name: Optional[str] = Field(None, description="팀 이름", max_length=100)
    e_team_name: Optional[str] = Field(None, description="팀 영문 이름", max_length=100)
    orig_yyyy: Optional[str] = Field(None, description="창단 연도", max_length=4)
    zip_code1: Optional[str] = Field(None, description="우편번호 앞자리", max_length=10)
    zip_code2: Optional[str] = Field(None, description="우편번호 뒷자리", max_length=10)
    address: Optional[str] = Field(None, description="주소")
    ddd: Optional[str] = Field(None, description="지역번호", max_length=10)
    tel: Optional[str] = Field(None, description="전화번호", max_length=20)
    fax: Optional[str] = Field(None, description="팩스번호", max_length=20)
    homepage: Optional[str] = Field(None, description="홈페이지")
    owner: Optional[str] = Field(None, description="구단주", max_length=100)

    model_config = {"from_attributes": True}


class TeamCreateModel(BaseModel):
    """팀 생성 요청 모델."""

    stadium_id: Optional[int] = Field(None, description="경기장 ID")
    team_code: Optional[str] = Field(None, description="팀 코드", max_length=10)
    region_name: Optional[str] = Field(None, description="지역명", max_length=50)
    team_name: Optional[str] = Field(None, description="팀 이름", max_length=100)
    e_team_name: Optional[str] = Field(None, description="팀 영문 이름", max_length=100)
    orig_yyyy: Optional[str] = Field(None, description="창단 연도", max_length=4)
    zip_code1: Optional[str] = Field(None, description="우편번호 앞자리", max_length=10)
    zip_code2: Optional[str] = Field(None, description="우편번호 뒷자리", max_length=10)
    address: Optional[str] = Field(None, description="주소")
    ddd: Optional[str] = Field(None, description="지역번호", max_length=10)
    tel: Optional[str] = Field(None, description="전화번호", max_length=20)
    fax: Optional[str] = Field(None, description="팩스번호", max_length=20)
    homepage: Optional[str] = Field(None, description="홈페이지")
    owner: Optional[str] = Field(None, description="구단주", max_length=100)


class TeamUpdateModel(BaseModel):
    """팀 수정 요청 모델."""

    stadium_id: Optional[int] = Field(None, description="경기장 ID")
    team_code: Optional[str] = Field(None, description="팀 코드", max_length=10)
    region_name: Optional[str] = Field(None, description="지역명", max_length=50)
    team_name: Optional[str] = Field(None, description="팀 이름", max_length=100)
    e_team_name: Optional[str] = Field(None, description="팀 영문 이름", max_length=100)
    orig_yyyy: Optional[str] = Field(None, description="창단 연도", max_length=4)
    zip_code1: Optional[str] = Field(None, description="우편번호 앞자리", max_length=10)
    zip_code2: Optional[str] = Field(None, description="우편번호 뒷자리", max_length=10)
    address: Optional[str] = Field(None, description="주소")
    ddd: Optional[str] = Field(None, description="지역번호", max_length=10)
    tel: Optional[str] = Field(None, description="전화번호", max_length=20)
    fax: Optional[str] = Field(None, description="팩스번호", max_length=20)
    homepage: Optional[str] = Field(None, description="홈페이지")
    owner: Optional[str] = Field(None, description="구단주", max_length=100)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------


class ScheduleModel(BaseModel):
    """경기 일정 응답/직렬화 모델. SQLAlchemy Schedule ORM 대응."""

    id: Optional[int] = Field(None, description="경기 ID")
    stadium_id: Optional[int] = Field(None, description="경기장 ID")
    hometeam_id: Optional[int] = Field(None, description="홈팀 ID")
    awayteam_id: Optional[int] = Field(None, description="원정팀 ID")
    stadium_code: Optional[str] = Field(None, description="경기장 코드", max_length=10)
    sche_date: Optional[str] = Field(None, description="경기 일자 (YYYYMMDD)", max_length=8)
    gubun: Optional[str] = Field(None, description="경기 구분 (Y/N)", max_length=1)
    hometeam_code: Optional[str] = Field(None, description="홈팀 코드", max_length=10)
    awayteam_code: Optional[str] = Field(None, description="원정팀 코드", max_length=10)
    home_score: Optional[int] = Field(None, description="홈팀 점수")
    away_score: Optional[int] = Field(None, description="원정팀 점수")

    model_config = {"from_attributes": True}


class ScheduleCreateModel(BaseModel):
    """경기 일정 생성 요청 모델."""

    stadium_id: Optional[int] = Field(None, description="경기장 ID")
    hometeam_id: Optional[int] = Field(None, description="홈팀 ID")
    awayteam_id: Optional[int] = Field(None, description="원정팀 ID")
    stadium_code: Optional[str] = Field(None, description="경기장 코드", max_length=10)
    sche_date: Optional[str] = Field(None, description="경기 일자 (YYYYMMDD)", max_length=8)
    gubun: Optional[str] = Field(None, description="경기 구분 (Y/N)", max_length=1)
    hometeam_code: Optional[str] = Field(None, description="홈팀 코드", max_length=10)
    awayteam_code: Optional[str] = Field(None, description="원정팀 코드", max_length=10)
    home_score: Optional[int] = Field(None, description="홈팀 점수")
    away_score: Optional[int] = Field(None, description="원정팀 점수")


class ScheduleUpdateModel(BaseModel):
    """경기 일정 수정 요청 모델."""

    stadium_id: Optional[int] = Field(None, description="경기장 ID")
    hometeam_id: Optional[int] = Field(None, description="홈팀 ID")
    awayteam_id: Optional[int] = Field(None, description="원정팀 ID")
    stadium_code: Optional[str] = Field(None, description="경기장 코드", max_length=10)
    sche_date: Optional[str] = Field(None, description="경기 일자 (YYYYMMDD)", max_length=8)
    gubun: Optional[str] = Field(None, description="경기 구분 (Y/N)", max_length=1)
    hometeam_code: Optional[str] = Field(None, description="홈팀 코드", max_length=10)
    awayteam_code: Optional[str] = Field(None, description="원정팀 코드", max_length=10)
    home_score: Optional[int] = Field(None, description="홈팀 점수")
    away_score: Optional[int] = Field(None, description="원정팀 점수")
