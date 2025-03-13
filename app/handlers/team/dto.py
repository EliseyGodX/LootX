from datetime import datetime

from pydantic import Field

from app.config import TeamConfig
from app.db.enums import EnumAddons
from app.handlers.abc.dto import BaseDTO
from app.types import TeamId


class RequestCreateTeamDTO(BaseDTO):
    name: str = Field(..., min_length=TeamConfig.name_min_length,
                      max_length=TeamConfig.name_max_length)
    addon: EnumAddons
    password: str = Field(..., min_length=TeamConfig.password_min_length,
                          max_length=TeamConfig.password_max_length)


class RequestUpdateTeamDTO(BaseDTO):
    name: str | None = Field(None, min_length=TeamConfig.name_min_length,
                             max_length=TeamConfig.name_max_length)
    addon: EnumAddons | None = None
    password: str | None = Field(None, min_length=TeamConfig.password_min_length,
                                 max_length=TeamConfig.password_max_length)


class ResponseTeamDTO(BaseDTO):
    id: TeamId
    name: str
    addon: EnumAddons
    is_vip: bool
    vip_end: datetime | None
    owner_id: str
    password: str
