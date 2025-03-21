from datetime import datetime

from pydantic import BaseModel, Field

from app.config import AuthConfig, RaiderConfig, TeamConfig
from app.db.enums import EnumAddons, EnumClasses, EnumLanguages
from app.types import RaiderId, TeamId, UserId, Username, WoWItemId


class BaseDTO(BaseModel):
    ...


class RegistrationDTO(BaseDTO):
    username: str = Field(..., min_length=AuthConfig.username_min_length,
                          max_length=AuthConfig.username_max_length)
    email: str = Field(..., max_length=AuthConfig.email_max_length)
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)


class AuthDTO(BaseDTO):
    username: str = Field(..., min_length=AuthConfig.username_min_length,
                          max_length=AuthConfig.username_max_length)
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)


class ItemDTO(BaseDTO):
    id: WoWItemId
    wow_id: int
    addon: EnumAddons
    lang: EnumLanguages
    html_tooltip: str
    icon_url: str
    origin_link: str


class RaiderDTO(BaseDTO):
    id: RaiderId
    name: str
    team_id: TeamId
    class_name: EnumClasses
    is_active: bool


class QueueDTO(BaseDTO):
    position: int
    raider: RaiderDTO


class QueueListDTO(BaseDTO):
    team_id: TeamId
    wow_item_id: int
    queue: list[QueueDTO]


class CreateQueueDTO(BaseDTO):
    team_id: TeamId
    wow_item_id: int
    raiders: list[RaiderId]


class CreateRaiderDTO(BaseDTO):
    name: str = Field(..., min_length=RaiderConfig.name_min_length,
                      max_length=RaiderConfig.name_max_length)
    team_id: TeamId
    class_name: EnumClasses
    is_active: bool = True


class CreateTeamDTO(BaseDTO):
    name: str = Field(..., min_length=TeamConfig.name_min_length,
                      max_length=TeamConfig.name_max_length)
    addon: EnumAddons
    password: str = Field(..., min_length=TeamConfig.password_min_length,
                          max_length=TeamConfig.password_max_length)


class UpdateTeamDTO(BaseDTO):
    name: str | None = Field(None, min_length=TeamConfig.name_min_length,
                             max_length=TeamConfig.name_max_length)
    addon: EnumAddons | None = None
    password: str | None = Field(None, min_length=TeamConfig.password_min_length,
                                 max_length=TeamConfig.password_max_length)


class TeamDTO(BaseDTO):
    id: TeamId
    name: str
    addon: EnumAddons
    is_vip: bool
    vip_end: datetime | None
    owner_id: str


class ChangeUserPasswordDTO(BaseDTO):
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)


class UserDTO(BaseDTO):
    id: UserId
    username: Username
    email: str
    is_active: bool


class LogDTO(BaseDTO):
    created_at: datetime
    queue: list[QueueDTO]


class LogListDTO(BaseDTO):
    team_id: TeamId
    wow_item_id: int | None
    limit: int | None
    offset: int | None
    logs: list[LogDTO]


class FullTeamDTO(BaseDTO):
    team: TeamDTO
    owner: UserDTO
    queues: list[QueueListDTO]
