# flake8-in-file-ignores: noqa: WPS201

import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from dotenv import load_dotenv
from kapusta import AlchemyCRUD
from litestar.openapi.plugins import SwaggerRenderPlugin

from app.caches.base import RedisAsyncCache
from app.caches.configs import RedisConfig
from app.db.sqlalchemy.base import AsyncSQLAlchemyDB
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
from app.db.wow_api.base import WoWHeadAPI
from app.db.wow_api.configs import WoWHeadAPIConfig
from app.mailers.base import AsyncSMTPMailer
from app.mailers.configs import SMTPConfig
from app.task_managers.base import KapustaTaskManager
from app.task_managers.configs import KapustaConfig
from app.tokens.base import JWToken
from app.tokens.configs import JWTokenConfig


class Language(Enum):
    ru = 'ru'
    de = 'de'
    en = 'en'
    es = 'es'
    fr = 'fr'
    it = 'it'
    pt = 'pt'
    ko = 'ko'
    cn = 'cn'


SERVICE_NAME = 'LootX'
VERSION = '0.0.0'

APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent

load_dotenv(ROOT_PATH / '.env')

allow_origins = os.getenv('ALLOW_ORIGINS').split(",")  # type: ignore

file_handler = logging.FileHandler(ROOT_PATH / f"{SERVICE_NAME}.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter(
        '%(levelname)s | %(asctime)s | %(module)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
)
logger = logging.getLogger(SERVICE_NAME)
logger.addHandler(file_handler)


DATABASE_URL: str = os.getenv('DATABASE_URL')  # type: ignore

open_api_render_plugins = [SwaggerRenderPlugin()]


EMAIL_REGISTRATION_SUBJECT: Mapping[Language, str] = MappingProxyType({
    Language.en: 'Registration'
})
EMAIL_REGISTRATION_BODY: Mapping[Language, str] = MappingProxyType({
    Language.en: '{}'
})

EMAIL_CHANGE_PASSWORD_SUBJECT: Mapping[Language, str] = MappingProxyType({
    Language.en: 'change password'
})
EMAIL_CHANGE_PASSWORD_BODY: Mapping[Language, str] = MappingProxyType({
    Language.en: '{}'
})

EMAIL_DELETE_TEAM_SUBJECT: Mapping[Language, str] = MappingProxyType({
    Language.en: 'delete team'
})
EMAIL_DELETE_TEAM_BODY: Mapping[Language, str] = MappingProxyType({
    Language.en: '{}'
})

DataBase = AsyncSQLAlchemyDB
DataBaseConfig = SQLAlchemyDBConfig(
    db_url=DATABASE_URL,
    session_maker_kwargs={'expire_on_commit': False}
)

Cache = RedisAsyncCache
CacheConfig = RedisConfig(
    logger=logger,
    redis_host=os.getenv('REDIS_HOST'),  # type: ignore
    redis_port=int(os.getenv('REDIS_PORT'))  # type: ignore
)

Mailer = AsyncSMTPMailer
MailerConfig = SMTPConfig(
    logger=logger,
    self_email=os.getenv('SELF_EMAIL'),  # type: ignore
    smtp_server=os.getenv('EMAIL_SERVER'),  # type: ignore
    smtp_user=os.getenv('EMAIL_USER'),  # type: ignore
    smtp_password=os.getenv('EMAIL_PASSWORD'),  # type: ignore
    smtp_port=int(os.getenv('SMTP_PORT'))  # type: ignore
)

Token = JWToken
TokenConfigType = JWTokenConfig
TokenConfig = TokenConfigType(
    alg=os.getenv('JWT_ALGORITHM'),  # type: ignore
    typ='JWT',
    key=os.getenv('JWT_KEY'),  # type: ignore
)

TaskManager = KapustaTaskManager
TaskManagerConfig = KapustaConfig(
    crud=AlchemyCRUD(DATABASE_URL),
    logger=logger,
    max_tick_interval=5 * 60,
    default_overdue_time_delta=None,
    default_max_retry_attempts=3,
    default_timeout=0
)

WoWAPI = WoWHeadAPI
WoWAPIConfig = WoWHeadAPIConfig(
    logger=logger,
    url='https://www.wowhead.com/{addon}/{lang}/item={id}&xml',
    icon_url='https://wow.zamimg.com/images/wow/icons/large/{icon}.jpg'
)


@dataclass(frozen=True)
class BaseConfig:
    ...


@dataclass(frozen=True)
class AuthConfig(BaseConfig):
    username_min_length: int = 2
    username_max_length: int = 12
    email_max_length: int = 256
    password_min_length: int = 5
    password_max_length: int = 24

    registration_token_exp: timedelta = timedelta(minutes=5)
    access_token_exp: timedelta = timedelta(hours=1)
    refresh_token_exp: timedelta = timedelta(weeks=5)

    del_inactive_user_after: timedelta = timedelta(minutes=5)


@dataclass(frozen=True)
class TeamConfig(BaseConfig):
    name_min_length: int = 2
    name_max_length: int = 24
    password_min_length: int = 5
    password_max_length: int = 24

    delete_team_token_exp: timedelta = timedelta(minutes=5)


@dataclass(frozen=True)
class UserConfig(BaseConfig):
    change_password_token_exp: timedelta = timedelta(minutes=5)


@dataclass(frozen=True)
class RaiderConfig(BaseConfig):
    name_min_length: int = 2
    name_max_length: int = 12


@dataclass(frozen=True)
class ItemConfig(BaseConfig):
    ...


@dataclass(frozen=True)
class QueueConfig(BaseConfig):
    ...
