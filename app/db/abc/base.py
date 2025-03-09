from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Literal, TypeVar

from app.db.abc.configs import BaseDBConfig
from app.db.abc.models import TeamProtocol, UserProtocol
from app.db.enums import EnumAddons
from app.types import Sentinel, UserId, Username

DBConfig = TypeVar('DBConfig', bound=BaseDBConfig)


@dataclass
class BaseAsyncDB(ABC, Generic[DBConfig]):
    config: DBConfig

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def create_user(self, username: str, password: str,
                          email: str, is_active: bool,
                          id: UserId = Sentinel) -> UserProtocol: ...

    @abstractmethod
    async def del_user(self, id: UserId) -> None: ...

    @abstractmethod
    async def is_user_username_email_unique(self, username: str, email: str
                                            ) -> Literal[True]: ...

    @abstractmethod
    async def is_user_active(self, id: UserId) -> bool: ...

    @abstractmethod
    async def activate_user(self, username: Username) -> UserId: ...

    @abstractmethod
    async def create_team(self, name: str, addon: EnumAddons, vip_end: datetime | None,
                          owner_id: str, password: str, id: str = Sentinel
                          ) -> TeamProtocol: ...

    @abstractmethod
    async def del_team(self, id: str) -> None: ...

    @abstractmethod
    async def get_team(self, name: str | None = Sentinel,
                       id: str | None = Sentinel) -> TeamProtocol: ...

    @abstractmethod
    async def update_team(self, id: str, name: str = Sentinel,
                          addon: EnumAddons = Sentinel, is_vip: bool = Sentinel,
                          vip_end: datetime = Sentinel, password: str = Sentinel,
                          ) -> TeamProtocol: ...

    @abstractmethod
    async def close(self) -> None: ...
