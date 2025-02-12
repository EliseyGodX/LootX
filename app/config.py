import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from dotenv import load_dotenv
from litestar.contrib.jinja import JinjaTemplateEngine

from app.cache import RedisAsyncCache
from app.mail import AsyncSMTPMailer

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
JWT_KEY: str = os.getenv('JWT_KEY')  # type: ignore[reportArgumentType]
JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM')  # type: ignore[reportArgumentType]
REGISTRATION_TOKEN_EXP = timedelta(minutes=5)


SELF_EMAIL: str = os.getenv('SELF_EMAIL')  # type: ignore[reportArgumentType]
EMAIL_SERVER: str = os.getenv('EMAIL_SERVER')  # type: ignore[reportArgumentType]
EMAIL_USER: str = os.getenv('EMAIL_USER')  # type: ignore[reportArgumentType]
EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD')  # type: ignore[reportArgumentType]
SMTP_PORT: int = int(os.getenv('SMTP_PORT'))  # type: ignore[reportArgumentType]


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


MAILER_TYPE = AsyncSMTPMailer

EMAIL_REGISTRATION_SUBJECT: Mapping[Language, str] = MappingProxyType({
    Language.en: 'Registration'
})

EMAIL_REGISTRATION_BODY: Mapping[Language, str] = MappingProxyType({
    Language.en: '{}'
})


CACHE_TYPE = RedisAsyncCache

CACHE_CONFIG: Mapping[str, Any] = MappingProxyType({
    "logger": logger
})

EMAIL_CONFIG: Mapping[str, Any] = MappingProxyType({
    "self_email": SELF_EMAIL,
    "logger": logger,
    "service_name": SERVICE_NAME,
    "smtp_server": EMAIL_SERVER,
    "smtp_user": EMAIL_USER,
    "smtp_password": EMAIL_PASSWORD,
    "smtp_port": SMTP_PORT
})


TEMPLATE_CONFIG: Mapping[str, Any] = MappingProxyType({
    'directory': APP_PATH / 'templates',
    'engine': JinjaTemplateEngine
})


@dataclass(frozen=True)
class AuthConfig:
    username_min_length: int = 2
    username_max_length: int = 12
    email_max_length: int = 256
    password_min_length: int = 5
    password_max_length: int = 24
