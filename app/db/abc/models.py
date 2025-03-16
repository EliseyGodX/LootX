# flake8-in-file-ignores: noqa: WPS110

from datetime import datetime
from typing import Protocol

from app.db.enums import EnumAddons, EnumClasses, EnumLanguages
from app.types import WoWItemId, LogId, QueueId, RaiderId, TeamId, UserId


class UserProtocol(Protocol):
    id: UserId
    username: str
    email: str
    is_active: bool
    password: str
    teams: list['TeamProtocol']
    logs: list['LogProtocol']


class TeamProtocol(Protocol):
    id: TeamId
    name: str
    addon: EnumAddons
    is_vip: bool
    vip_end: datetime | None
    owner_id: UserId
    password: str
    owner: 'UserProtocol'
    raiders: list['RaiderProtocol']
    logs: list['LogProtocol']
    queues: list['QueueProtocol']


class RaiderProtocol(Protocol):
    id: RaiderId
    name: str
    team_id: TeamId
    class_name: EnumClasses
    is_active: bool
    team: 'TeamProtocol'
    queues: list['QueueProtocol']


class WoWItemProtocol(Protocol):
    id: WoWItemId
    wow_id: int
    addon: EnumAddons
    lang: EnumLanguages
    html_tooltip: str
    icon_url: str
    origin_link: str
    logs: list['LogProtocol']
    queues: list['QueueProtocol']


class QueueProtocol(Protocol):
    id: QueueId
    position: int
    team_id: TeamId
    raider_id: RaiderId
    item_id: WoWItemId
    team: 'TeamProtocol'
    raider: 'RaiderProtocol'
    item: 'WoWItemProtocol'


class LogProtocol(Protocol):
    id: LogId
    team_id: TeamId
    user_id: UserId
    item_id: WoWItemId
    data: str
    team: 'TeamProtocol'
    user: 'UserProtocol'
    item: 'WoWItemProtocol'
