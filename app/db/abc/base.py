from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Literal, TypeVar

from ulid import ULID

from app.db.abc.configs import BaseDBConfig
from app.db.abc.models import (RaiderProtocol, TeamProtocol, UserProtocol,
                               WoWItemProtocol)
from app.db.enums import EnumAddons, EnumLanguages
from app.db.wow_api.base import BaseAsyncWoWAPI
from app.types import RaiderId, Sentinel, TeamId, UserId, Username, WoWItemId

DBConfig = TypeVar('DBConfig', bound=BaseDBConfig)


def get_id() -> str:
    return str(ULID())


@dataclass
class BaseAsyncDB(ABC, Generic[DBConfig]):
    config: DBConfig

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def create_user(
        self, username: str, password: str, email: str, is_active: bool,
        id: UserId = Sentinel
    ) -> UserProtocol: ...

    @abstractmethod
    async def get_user(self, id: UserId) -> UserProtocol: ...

    @abstractmethod
    async def get_user_by_username(self, username: Username) -> UserProtocol: ...

    @abstractmethod
    async def get_user_email(self, id: UserId) -> str: ...

    @abstractmethod
    async def del_user(self, id: UserId) -> None: ...

    @abstractmethod
    async def change_user_password(self, id: UserId, new_password: str) -> None: ...

    @abstractmethod
    async def is_user_username_email_unique(
        self, username: str, email: str
    ) -> Literal[True]: ...

    @abstractmethod
    async def is_user_active(self, id: UserId) -> bool: ...

    @abstractmethod
    async def activate_user(self, username: Username) -> UserId: ...

    @abstractmethod
    async def create_team(
        self, name: str, addon: EnumAddons, owner_id: str, password: str,
        id: TeamId = Sentinel, vip_end: datetime | None = None,
        is_vip: bool | None = None
    ) -> TeamProtocol: ...

    @abstractmethod
    async def del_team(self, id: TeamId) -> None: ...

    @abstractmethod
    async def get_team_by_name(self, name: str) -> TeamProtocol: ...

    @abstractmethod
    async def get_team(self, id: TeamId) -> TeamProtocol: ...

    @abstractmethod
    async def update_team(
        self, id: TeamId, name: str | None = None, addon: EnumAddons | None = None,
        is_vip: bool | None = None, vip_end: datetime | None = None,
        password: str | None = None
    ) -> TeamProtocol: ...

    @abstractmethod
    async def get_team_by_name_with_owner(self, team_name: str) -> TeamProtocol: ...

    @abstractmethod
    async def get_team_with_owner(self, team_id: str) -> TeamProtocol: ...

    @abstractmethod
    async def verify_username_password(
        self, username: Username, password: str
    ) -> UserId: ...

    @abstractmethod
    async def set_raider_inactive(self, id: RaiderId) -> None: ...

    @abstractmethod
    async def get_raider(self, id: RaiderId) -> RaiderProtocol: ...

    @abstractmethod
    async def get_wow_item(self, id: WoWItemId) -> WoWItemProtocol: ...

    @abstractmethod
    async def get_wow_item_by_wow_id(
        self, wow_id: int, addon: EnumAddons, lang: EnumLanguages,
        wow_api: BaseAsyncWoWAPI
    ) -> WoWItemProtocol | None: ...

    @abstractmethod
    async def close(self) -> None: ...
