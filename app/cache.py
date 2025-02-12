import abc
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Self, TypeAlias

from redis import asyncio as aioredis
from redis.typing import EncodableT

Seconds: TypeAlias = int


@dataclass(kw_only=True)
class BaseAsyncTTLCache(abc.ABC):
    logger: logging.Logger
    default_cache_lifetime: Seconds | timedelta = 60

    @abc.abstractmethod
    async def connect(self) -> Self: ...

    @abc.abstractmethod
    async def set(self, key: str, value: EncodableT,  # noqa: WPS110
                  time: Optional[Seconds | timedelta] = None) -> None: ...

    @abc.abstractmethod
    async def get(self, key: str) -> bytes | None: ...

    @abc.abstractmethod
    async def close(self) -> None: ...


@dataclass(kw_only=True)
class RedisAsyncCache(BaseAsyncTTLCache):
    redis_host: str = "localhost"
    redis_port: int = 6379

    async def connect(self) -> Self:
        self.redis = aioredis.Redis(host=self.redis_host, port=self.redis_port)
        return self

    async def set(self, key: str, value: EncodableT,  # noqa: WPS11
                  time: Optional[Seconds | timedelta] = None) -> None:
        try:
            await self.redis.set(name=key,
                                 value=value,
                                 ex=time if time else self.default_cache_lifetime
                                 )
        except Exception as e:
            self.logger.warning(e)

    async def get(self, key: str) -> bytes | None:
        try:
            return await self.redis.get(name=key)
        except Exception as e:
            self.logger.warning(e)

    async def close(self) -> None:
        await self.redis.close()
