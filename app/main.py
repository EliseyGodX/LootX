# flake8-in-file-ignores: noqa: WPS201

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

from app.cache import BaseAsyncTTLCache
from app.config import (APP_PATH, CACHE_CONFIG, CACHE_TYPE, EMAIL_CONFIG,
                        MAILER_TYPE, TEMPLATE_CONFIG)
from app.controllers import AuthController
from app.db.base import DatabaseError
from app.dependencies import get_language
from app.mail import BaseAsyncMailer, MailerError


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:
    app.state.cache = CACHE_TYPE(**CACHE_CONFIG)
    app.state.mailer = MAILER_TYPE(**EMAIL_CONFIG)
    await app.state.cache.connect()
    await app.state.mailer.connect()

    yield

    await app.state.cache.close()
    await app.state.mailer.close()


def provide_cache() -> BaseAsyncTTLCache:
    return app.state.cache


def provide_mailer() -> BaseAsyncMailer:
    return app.state.mailer


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
        'cache': Provide(provide_cache, sync_to_thread=False),
        'mailer': Provide(provide_mailer, sync_to_thread=False),
        'lang': Provide(get_language, sync_to_thread=False)
    },
    lifespan=[lifespan],
    exception_handlers={
        DatabaseError: database_exc_handler,
        MailerError: mailer_exc_handler
    },
)
