from contextlib import asynccontextmanager
from typing import AsyncIterator

from litestar import Litestar, get
from litestar.di import Provide
from litestar.response import Template
from litestar.static_files.config import StaticFilesConfig
from litestar.template.config import TemplateConfig

from app.cache import BaseAsyncTTLCache, RedisAsyncCache
from app.config import APP_PATH, CACHE_CONFIG, EMAIL_CONFIG, TEMPLATE_CONFIG
from app.mail import AsyncSMTPEmail, BaseAsyncEmail


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncIterator[None]:
    app.state.cache = RedisAsyncCache(**CACHE_CONFIG)
    app.state.email = AsyncSMTPEmail(**EMAIL_CONFIG)
    await app.state.cache.connect()
    await app.state.email.connect()

    yield

    await app.state.cache.close()
    await app.state.email.close()


async def provide_cache(app: Litestar) -> BaseAsyncTTLCache:
    return app.state.cache


async def provide_email(app: Litestar) -> BaseAsyncEmail:
    return app.state.email


@get('/')
async def index() -> Template:
    return Template(template_name='edit.html')


@get('/registration', sync_to_thread=False)
def registration() -> Template:
    return Template(template_name='registration.html')


app = Litestar(
    route_handlers=[index, registration],
    template_config=TemplateConfig(**TEMPLATE_CONFIG),
    debug=True,
    static_files_config=[
        StaticFilesConfig(directories=[APP_PATH / 'static'], path='/static')
    ],
    dependencies={
        'cache': Provide(provide_cache),
        'emai': Provide(provide_email)
    },
    lifespan=[lifespan],
)
