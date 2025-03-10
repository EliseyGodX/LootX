from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Literal, TypeVar

from ulid import ULID

from app.db.abc.configs import BaseDBConfig
from app.db.abc.models import TeamProtocol, UserProtocol
from app.db.enums import EnumAddons
from app.types import Sentinel, UserId, Username

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
    async def del_user(self, id: UserId) -> None: ...

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
        id: str = Sentinel, vip_end: datetime | None = None, is_vip: bool | None = None
    ) -> TeamProtocol: ...

    @abstractmethod
    async def del_team(self, id: str) -> None: ...

    @abstractmethod
    async def get_team_by_name(self, name: str) -> TeamProtocol: ...

    @abstractmethod
    async def get_team(self, id: str) -> TeamProtocol: ...

    @abstractmethod
    async def update_team(
        self, id: str, name: str = Sentinel, addon: EnumAddons = Sentinel,
        is_vip: bool = Sentinel, vip_end: datetime = Sentinel, password: str = Sentinel,
    ) -> TeamProtocol: ...

    @abstractmethod
    async def verify_username_password(
        self, username: Username, password: str
    ) -> UserId: ...

    @abstractmethod
    async def close(self) -> None: ...
