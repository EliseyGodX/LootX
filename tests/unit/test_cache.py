# flake8-in-file-ignores: noqa: WPS432

import logging

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.redis import RedisContainer

from app.caches.base import BaseAsyncTTLCache, RedisAsyncCache
from app.caches.configs import BaseTTLCacheConfig, RedisConfig


def update_config(config: BaseTTLCacheConfig, testcontainer: DockerContainer) -> None:
    config_type = type(config)
    if config_type == RedisConfig:
        config.redis_host = testcontainer.get_container_host_ip()  # type: ignore
        config.redis_port = testcontainer.get_exposed_port(6379)  # type: ignore


@pytest.mark.parametrize(
    argnames='cache_type, config, testcontainer',
    argvalues=[
        [
            RedisAsyncCache,
            RedisConfig(
                logger=logging.getLogger('redis'),
                redis_host='',
                redis_port=0
            ),
            RedisContainer()
        ]
    ]
)
@pytest.mark.asyncio
async def test_cache(
    cache_type: type[BaseAsyncTTLCache], config: BaseTTLCacheConfig,
    testcontainer: DockerContainer
) -> None:
    with testcontainer as container:
        update_config(config, container)
        cache = cache_type(config)
        await cache.connect()

        await cache.set('key', 'value')
        fetched_value = await cache.get('key')
        assert fetched_value == 'value', f"Expected 'value', got {fetched_value}"

        await cache.del_key('key')
        after_delete = await cache.get('key')
        assert after_delete is None, f"Expected None, got {after_delete}"

        await cache.close()
