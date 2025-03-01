from datetime import datetime
from typing import Protocol

from app.db.enums import EnumAddons, EnumClasses
from app.types import UserId


class UserProtocol(Protocol):
    id: UserId
    username: str
    email: str
    is_active: bool
    password: str


class TeamProtocol(Protocol):
    id: str
    name: str
    addon: EnumAddons
    is_vip: bool
    vip_end: datetime | None
    owner_id: str
    password: str


class RaiderProtocol(Protocol):
    id: str
    name: str
    team_id: str
    class_name: EnumClasses


class ItemProtocol(Protocol):  # noqa: WPS110
    id: str
    wow_id: int
    html_tooltip: str
    icon_id: str


class QueueProtocol(Protocol):
    id: str
    position: int
    team_id: str
    raider_id: str
    item_id: str


class LogProtocol(Protocol):
    id: str
    team_id: str
    user_id: str
    item_id: str
    sequence: str
