# flake8-in-file-ignores: noqa: WPS201, WPS202, WPS203

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, NoReturn

from litestar import Litestar, Request
from litestar import status_codes as status
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.openapi import OpenAPIConfig

from app.caches.base import BaseAsyncTTLCache
from app.config import (SERVICE_NAME, VERSION, Cache, CacheConfig, CacheKeys,
                        DataBase, DataBaseConfig, Mailer, MailerConfig,
                        TaskManager, TaskManagerConfig, Token, TokenConfig,
                        WoWAPI, WoWAPIConfig, allow_origins, logging_config,
                        open_api_render_plugins)
from app.db.abc.base import BaseAsyncDB
from app.db.exc import DatabaseError
from app.db.wow_api.base import BaseAsyncWoWAPI
from app.dependencies import auth_client, get_language
from app.handlers.auth import AuthController
from app.handlers.core import CoreController
from app.handlers.item import ItemController
from app.handlers.log import LogController
from app.handlers.queue import QueueController
from app.handlers.raider import RaiderController
from app.handlers.team import TeamController
from app.handlers.user import UserController
from app.mailers.base import BaseAsyncMailer, MailerError
from app.task_managers.base import BaseAsyncTaskManager, Tasks
from app.tokens.base import BaseToken
from app.tokens.configs import BaseTokenConfig
from app.tokens.payloads import AccessTokenPayload
from app.types import UserId

logger = logging.getLogger('app.main')


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:  # noqa: WPS213
    app.state.db = DataBase(DataBaseConfig)
    app.state.cache = Cache(CacheConfig)
    app.state.cache_keys = CacheKeys()
    app.state.mailer = Mailer(MailerConfig)
    app.state.wow_api = WoWAPI(WoWAPIConfig)
    app.state.task_manager = TaskManager(
        TaskManagerConfig,
        Tasks(
            del_inactive_user=del_inactive_user_task
        )
    )
    app.state.token_type = Token
    app.state.token_config = TokenConfig
    await app.state.db.connect()
    await app.state.cache.connect()
    await app.state.mailer.connect()
    await app.state.wow_api.connect()
    await app.state.task_manager.connect()

    logger.info(f'{SERVICE_NAME}: App started')
    yield

    await app.state.db.close()
    await app.state.cache.close()
    await app.state.mailer.close()
    await app.state.wow_api.close()
    await app.state.task_manager.close()


async def del_inactive_user_task(user_id: UserId) -> None:
    if not await provide_db().is_user_active(user_id):
        await provide_db().del_user(user_id)


def provide_db() -> BaseAsyncDB:
    return app.state.db


def provide_cache() -> BaseAsyncTTLCache:
    return app.state.cache


def provide_cache_keys() -> dict[str, str]:
    return app.state.cache_keys


def provide_mailer() -> BaseAsyncMailer:
    return app.state.mailer


def provide_token_type() -> type[BaseToken]:
    return app.state.token_type


def provide_token_config() -> BaseTokenConfig:
    return app.state.token_config


def provide_wow_api() -> BaseAsyncWoWAPI:
    return app.state.wow_api


def provide_task_manager() -> BaseAsyncTaskManager:
    return app.state.task_manager


def provide_auth_client_dep(request: Request) -> AccessTokenPayload:
    return auth_client(
        request=request,
        token_type=provide_token_type(),
        token_config=provide_token_config()
    )


def database_exc_handler(request: Request, exc: DatabaseError) -> NoReturn:
    logger.critical('DataBase error:', exc, exc_info=True)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def mailer_exc_handler(request: Request, exc: MailerError) -> NoReturn:
    logger.critical('Mailer error:', exc, exc_info=True)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


app = Litestar(
    route_handlers=[AuthController, TeamController, UserController, RaiderController,
                    ItemController, QueueController, LogController, CoreController],
    openapi_config=OpenAPIConfig(
        title=f'{SERVICE_NAME} API',
        version=VERSION,
        render_plugins=open_api_render_plugins
    ),
    dependencies={
        'db': Provide(provide_db, sync_to_thread=False),
        'cache': Provide(provide_cache, sync_to_thread=False),
        'cache_keys': Provide(provide_cache_keys, sync_to_thread=False),
        'mailer': Provide(provide_mailer, sync_to_thread=False),
        'task_manager': Provide(provide_task_manager, sync_to_thread=False),
        'wow_api': Provide(provide_wow_api, sync_to_thread=False),
        'token_type': Provide(provide_token_type, sync_to_thread=False),
        'token_config': Provide(provide_token_config, sync_to_thread=False),
        'lang': Provide(get_language, sync_to_thread=False),
        'auth_client': Provide(provide_auth_client_dep, sync_to_thread=False)
    },
    lifespan=[lifespan],
    exception_handlers={
        DatabaseError: database_exc_handler,
        MailerError: mailer_exc_handler
    },
    cors_config=CORSConfig(allow_origins=allow_origins),
    logging_config=logging_config
)
