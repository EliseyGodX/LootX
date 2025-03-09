from datetime import datetime

from pydantic import BaseModel, Field

from app.config import TeamsConfig
from app.db.enums import EnumAddons


class RequestCreateTeamDTO(BaseModel):
    name: str = Field(..., min_length=TeamsConfig.team_name_min_length,
                      max_length=TeamsConfig.team_name_max_length)
    addon: EnumAddons
    password: str = Field(..., min_length=TeamsConfig.password_min_length,
                          max_length=TeamsConfig.password_max_length)


class RequestUpdateTeamDTO(BaseModel):
    name: str | None = None
    addon: EnumAddons | None = None
    is_vip: bool | None = None
    vip_end: datetime | None = None
    password: str | None = Field(None, min_length=TeamsConfig.password_min_length,
                                 max_length=TeamsConfig.password_max_length)


class ResponseTeamDTO(BaseModel):
    name: str
    addon: EnumAddons
    is_vip: bool
    vip_end: datetime | None
    owner_id: str
    password: str
