from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from app.db.abc.configs import BaseDBConfig
from app.db.abc.models import UserProtocol
from app.types import Sentinel, UserId

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
    async def close(self) -> None: ...
