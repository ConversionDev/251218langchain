"""Soccer Pydantic 전송 모델 (bases.soccer ORM 대응)."""

from domain.models.transfers.soccer_transfer import (  # type: ignore
    PlayerCreateModel,
    PlayerModel,
    PlayerUpdateModel,
    ScheduleCreateModel,
    ScheduleModel,
    ScheduleUpdateModel,
    StadiumCreateModel,
    StadiumModel,
    StadiumUpdateModel,
    TeamCreateModel,
    TeamModel,
    TeamUpdateModel,
)

__all__ = [
    "PlayerCreateModel",
    "PlayerModel",
    "PlayerUpdateModel",
    "ScheduleCreateModel",
    "ScheduleModel",
    "ScheduleUpdateModel",
    "StadiumCreateModel",
    "StadiumModel",
    "StadiumUpdateModel",
    "TeamCreateModel",
    "TeamModel",
    "TeamUpdateModel",
]
