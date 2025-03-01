# flake8-in-file-ignores: noqa: WPS201, WPS202

from contextlib import asynccontextmanager
from typing import AsyncIterator, NoReturn

from litestar import Litestar, Request
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.handlers import get
from litestar.response import Template
from litestar.static_files.config import StaticFilesConfig
from litestar.template.config import TemplateConfig

from app.caches.base import BaseAsyncTTLCache
from app.config import (APP_PATH, TEMPLATE_CONFIG, Cache, CacheConfig,
                        DataBase, DataBaseConfig, Mailer, MailerConfig,
                        TaskManager, TaskManagerConfig, Token, TokenConfig)
from app.controllers import AuthController
from app.db.abc.base import BaseAsyncDB
from app.db.exc import DatabaseError
from app.dependencies import get_language
from app.mailers.base import BaseAsyncMailer, MailerError
from app.task_managers.base import BaseAsyncTaskManager, Tasks
from app.tokens.base import BaseToken
from app.tokens.configs import BaseTokenConfig
from app.types import UserId


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:
    app.state.db = DataBase(DataBaseConfig)
    app.state.cache = Cache(CacheConfig)
    app.state.mailer = Mailer(MailerConfig)
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
    await app.state.task_manager.connect()

    yield

    await app.state.db.close()
    await app.state.cache.close()
    await app.state.mailer.close()
    await app.state.task_manager.close()


async def del_inactive_user_task(user_id: UserId) -> None:
    if not await provide_db().is_user_active(user_id):
        await provide_db().del_user(user_id)


def provide_db() -> BaseAsyncDB:
    return app.state.db


def provide_cache() -> BaseAsyncTTLCache:
    return app.state.cache


def provide_mailer() -> BaseAsyncMailer:
    return app.state.mailer


def provide_token_type() -> type[BaseToken]:
    return app.state.token_type


def provide_token_config() -> BaseTokenConfig:
    return app.state.token_config


def provide_task_manager() -> BaseAsyncTaskManager:
    return app.state.task_manager


@get('/')
async def index() -> Template:
    return Template(template_name='edit.html')


def database_exc_handler(request: Request, exc: DatabaseError) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def mailer_exc_handler(request: Request, exc: MailerError) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


app = Litestar(
    route_handlers=[index, AuthController],
    template_config=TemplateConfig(**TEMPLATE_CONFIG),
    debug=True,
    static_files_config=[
        StaticFilesConfig(directories=[APP_PATH / 'static'], path='/static')
    ],
    dependencies={
        'db': Provide(provide_db, sync_to_thread=False),
        'cache': Provide(provide_cache, sync_to_thread=False),
        'mailer': Provide(provide_mailer, sync_to_thread=False),
        'task_manager': Provide(provide_task_manager, sync_to_thread=False),
        'token_type': Provide(provide_token_type, sync_to_thread=False),
        'token_config': Provide(provide_token_config, sync_to_thread=False),
        'lang': Provide(get_language, sync_to_thread=False)
    },
    lifespan=[lifespan],
    exception_handlers={
        DatabaseError: database_exc_handler,
        MailerError: mailer_exc_handler
    },
)
