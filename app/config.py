# flake8-in-file-ignores: noqa: WPS201

import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from dotenv import load_dotenv
from kapusta import AlchemyCRUD
from litestar.contrib.jinja import JinjaTemplateEngine

from app.caches.base import RedisAsyncCache
from app.caches.configs import RedisConfig
from app.db.sqlalchemy.base import AsyncSQLAlchemyDB
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
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

APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent

load_dotenv(ROOT_PATH / '.env')


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


DATABASE_URL: str = os.getenv('DATABASE_URL')  # type: ignore[reportArgumentType]

CELERY_BROKER_URL: str = os.getenv(
    'CELERY_BROKER_URL'
)  # type: ignore[reportArgumentType]

REGISTRATION_TOKEN_EXP = timedelta(minutes=5)

TEMPLATE_CONFIG: Mapping[str, Any] = MappingProxyType({
    'directory': APP_PATH / 'templates',
    'engine': JinjaTemplateEngine
})


EMAIL_REGISTRATION_SUBJECT: Mapping[Language, str] = MappingProxyType({
    Language.en: 'Registration'
})

EMAIL_REGISTRATION_BODY: Mapping[Language, str] = MappingProxyType({
    Language.en: '{}'
})

DataBase = AsyncSQLAlchemyDB
DataBaseConfig = SQLAlchemyDBConfig(
    db_url=DATABASE_URL
)

Cache = RedisAsyncCache
CacheConfig = RedisConfig(
    logger=logger
)

Mailer = AsyncSMTPMailer
MailerConfig = SMTPConfig(
    logger=logger,
    self_email=os.getenv('SELF_EMAIL'),  # type: ignore[reportArgumentType]
    smtp_server=os.getenv('EMAIL_SERVER'),  # type: ignore[reportArgumentType]
    smtp_user=os.getenv('EMAIL_USER'),  # type: ignore[reportArgumentType]
    smtp_password=os.getenv('EMAIL_PASSWORD'),  # type: ignore[reportArgumentType]
    smtp_port=int(os.getenv('SMTP_PORT'))  # type: ignore[reportArgumentType]
)

Token = JWToken
TokenConfigType = JWTokenConfig
TokenConfig = TokenConfigType(
    alg=os.getenv('JWT_ALGORITHM'),  # type: ignore[reportArgumentType]
    typ='JWT',
    key=os.getenv('JWT_KEY'),  # type: ignore[reportArgumentType]
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


@dataclass(frozen=True)
class AuthConfig:
    username_min_length: int = 2
    username_max_length: int = 12
    email_max_length: int = 256
    password_min_length: int = 5
    password_max_length: int = 24
    del_inactive_user_after: timedelta = timedelta(minutes=5)
