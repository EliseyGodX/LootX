import logging
import os
from datetime import timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from dotenv import load_dotenv
from litestar.contrib.jinja import JinjaTemplateEngine

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


SERVICE_HOST: str = os.getenv('SERVICE_HOST')  # type: ignore[reportArgumentType]
DATABASE_URL: str = os.getenv('DATABASE_URL')  # type: ignore[reportArgumentType]
JWT_KEY: str = os.getenv('JWT_KEY')  # type: ignore[reportArgumentType]
JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM')  # type: ignore[reportArgumentType]

REGISTRATION_TOKEN_EXP = timedelta(minutes=5)
SELF_EMAIL = ''
SELF_EMAIL_SERVER = ''
SELF_EMAIL_USER = ''
SELF_EMAIL_PASSWORD = ''

EMAIL_REGISTRATION_MESSAGE: Mapping[str, str] = MappingProxyType({
    'eng': '{}'
})

CACHE_CONFIG: Mapping[str, Any] = MappingProxyType({
    "logger": logger
})

EMAIL_CONFIG: Mapping[str, Any] = MappingProxyType({
    "logger": logger,
    "smtp_server": SELF_EMAIL_SERVER,
    "smtp_user": SELF_EMAIL_USER,
    "smtp_password": SELF_EMAIL_PASSWORD
})

TEMPLATE_CONFIG: Mapping[str, Any] = MappingProxyType({
    'directory': APP_PATH / 'templates',
    'engine': JinjaTemplateEngine
})
