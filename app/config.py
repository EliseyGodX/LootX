# flake8-in-file-ignores: noqa: WPS201

import logging
import os
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from pathlib import Path
from types import MappingProxyType

from dotenv import load_dotenv
from kapusta import AlchemyCRUD
from litestar.config.cors import CORSConfig
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
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

SERVICE_NAME = 'LootX'
VERSION = '0.0.0'


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


APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent

load_dotenv(ROOT_PATH / '.env')

cors_config = CORSConfig(
    allow_origins=os.getenv('ALLOW_ORIGINS').split(',')  # type: ignore
)

logging_config = LoggingConfig(
    root={
        'level': 'DEBUG',
        'handlers': ['file']
    },
    handlers={
        'file': {
            'class': 'logging.FileHandler',
            'filename': ROOT_PATH / f"{SERVICE_NAME}.log",
            'mode': 'w',
            'formatter': 'standard',
        }
    },
    formatters={
        'standard': {
            'format': ('%(name)s | %(levelname)s | %(asctime)s'
                       ' | %(module)s | %(funcName)s | %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    log_exceptions='always',
)

openapi_config = OpenAPIConfig(
    title=f'{SERVICE_NAME} API',
    version=VERSION,
    render_plugins=[
        SwaggerRenderPlugin()
    ]
)

DATABASE_URL: str = os.getenv('DATABASE_URL')  # type: ignore

_db_logger = logging.getLogger('sqlalchemy.engine')
_db_logger.setLevel(logging.INFO)
DataBase = AsyncSQLAlchemyDB
DataBaseConfig = SQLAlchemyDBConfig(
    logger=_db_logger,
    db_url=DATABASE_URL,
    session_maker_kwargs={'expire_on_commit': False}
)

Cache = RedisAsyncCache
CacheConfig = RedisConfig(
    logger=logging.getLogger('redis'),
    redis_host=os.getenv('REDIS_HOST'),  # type: ignore
    redis_port=int(os.getenv('REDIS_PORT'))  # type: ignore
)


@dataclass(frozen=True)
class CacheKeys:
    team_name: str = 'tn: {}'
    full_team: str = 'ft: {}'


Mailer = AsyncSMTPMailer
MailerConfig = SMTPConfig(
    logger=logging.getLogger('smtp'),
    self_email=os.getenv('SELF_EMAIL'),  # type: ignore
    smtp_server=os.getenv('EMAIL_SERVER'),  # type: ignore
    smtp_user=os.getenv('EMAIL_USER'),  # type: ignore
    smtp_password=os.getenv('EMAIL_PASSWORD'),  # type: ignore
    smtp_port=int(os.getenv('SMTP_PORT'))  # type: ignore
)

Token = JWToken
TokenConfigType = JWTokenConfig
TokenConfig = TokenConfigType(
    logger=logging.getLogger('tokens'),
    alg=os.getenv('JWT_ALGORITHM'),  # type: ignore
    typ='JWT',
    key=os.getenv('JWT_KEY'),  # type: ignore
)

TaskManager = KapustaTaskManager
TaskManagerConfig = KapustaConfig(
    logger=logging.getLogger('kapusta'),
    crud=AlchemyCRUD(DATABASE_URL),
    max_tick_interval=5 * 60,
    default_overdue_time_delta=None,
    default_max_retry_attempts=3,
    default_timeout=0
)

WoWAPI = WoWHeadAPI
WoWAPIConfig = WoWHeadAPIConfig(
    logger=logging.getLogger('wow_head'),
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

    restricted_name_list: list[str] = field(default_factory=lambda: [
        'auth', 'core', 'item', 'log', 'queue', 'raider', 'team', 'user'
    ])

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


@dataclass(frozen=True)
class LogConfig(BaseConfig):
    ...


@dataclass(frozen=True)
class CoreConfig(BaseConfig):
    ...


EMAIL_REGISTRATION_SUBJECT = MappingProxyType({
    Language.en: 'LootX: Registration',
    Language.ru: 'LootX: Регистрация',
    Language.de: 'LootX: Registrierung',
    Language.es: 'LootX: Registro',
    Language.fr: 'LootX: Inscription',
    Language.it: 'LootX: Registrazione',
    Language.pt: 'LootX: Registro',
    Language.ko: 'LootX: 등록',
    Language.cn: 'LootX: 注册'
})

EMAIL_REGISTRATION_BODY = MappingProxyType({
    Language.en: (
        'To confirm your registration, visit '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Use the link within 5 minutes. Do not share it with anyone.'
    ),
    Language.ru: (
        'Для подтверждения регистрации перейдите по ссылке '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Перейдите по ссылке в течении 5 минут. Никому не передавайте её.'
    ),
    Language.de: (
        'Um Ihre Registrierung zu bestätigen, besuchen Sie '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Nutzen Sie den Link innerhalb von 5 Minuten. Geben Sie ihn niemandem weiter.'
    ),
    Language.es: (
        'Para confirmar su registro, visite '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Use el enlace en 5 minutos. No lo comparta con nadie.'
    ),
    Language.fr: (
        'Pour confirmer votre inscription, visitez '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Utilisez le lien dans les 5 minutes. Ne le partagez avec personne.'
    ),
    Language.it: (
        'Per confermare la registrazione, visita '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Usa il link entro 5 minuti. Non condividerlo con nessuno.'
    ),
    Language.pt: (
        'Para confirmar seu registro, visite '
        'http://localhost:8000/auth/verify-email/{}\n'
        'Use o link em 5 minutos. Não o compartilhe com ninguém.'
    ),
    Language.ko: (
        '등록을 확인하려면 http://localhost:8000/auth/verify-email/{} 에 방문하세요.\n'
        '5분 이내에 링크를 사용하세요. 다른 사람과 공유하지 마세요.'
    ),
    Language.cn: (
        '要确认您的注册，请访问 http://localhost:8000/auth/verify-email/{}\n'
        '请在 5 分钟内使用该链接。请勿与他人分享。'
    ),
})

EMAIL_CHANGE_PASSWORD_SUBJECT = MappingProxyType({
    Language.en: 'LootX: Change password',
    Language.ru: 'LootX: Смена пароля',
    Language.de: 'LootX: Passwort ändern',
    Language.es: 'LootX: Cambiar contraseña',
    Language.fr: 'LootX: Changer le mot de passe',
    Language.it: 'LootX: Cambia la password',
    Language.pt: 'LootX: Alterar senha',
    Language.ko: 'LootX: 비밀번호 변경',
    Language.cn: 'LootX: 更改密码'
})

EMAIL_CHANGE_PASSWORD_BODY = MappingProxyType({
    Language.en: (
        'To reset your password, visit '
        'http://localhost:8000/user/change-password/{}\n'
        'Use the link within 5 minutes.'
    ),
    Language.ru: (
        'Для смены пароля перейдите по ссылке '
        'http://localhost:8000/user/change-password/{}\n'
        'Перейдите по ссылке в течении 5 минут.'
    ),
    Language.de: (
        'Um Ihr Passwort zu ändern, besuchen Sie '
        'http://localhost:8000/user/change-password/{}\n'
        'Nutzen Sie den Link innerhalb von 5 Minuten.'
    ),
    Language.es: (
        'Para cambiar su contraseña, visite '
        'http://localhost:8000/user/change-password/{}\n'
        'Use el enlace en 5 minutos.'
    ),
    Language.fr: (
        'Pour changer votre mot de passe, visitez '
        'http://localhost:8000/user/change-password/{}\n'
        'Utilisez le lien dans les 5 minutes.'
    ),
    Language.it: (
        'Per cambiare la password, visita '
        'http://localhost:8000/user/change-password/{}\n'
        'Usa il link entro 5 minuti.'
    ),
    Language.pt: (
        'Para alterar sua senha, visite '
        'http://localhost:8000/user/change-password/{}\n'
        'Use o link em 5 minutos.'
    ),
    Language.ko: (
        '비밀번호를 변경하려면 '
        'http://localhost:8000/user/change-password/{} 에 방문하세요.\n'
        '5분 이내에 링크를 사용하세요.'
    ),
    Language.cn: (
        '要更改您的密码，请访问 '
        'http://localhost:8000/user/change-password/{}\n'
        '请在 5 分钟内使用该链接。'
    ),
})

EMAIL_DELETE_TEAM_SUBJECT = MappingProxyType({
    Language.en: 'delete team',
    Language.ru: 'LootX: Удаление команды',
    Language.de: 'LootX: Team löschen',
    Language.es: 'LootX: Eliminar equipo',
    Language.fr: 'LootX: Supprimer l’équipe',
    Language.it: 'LootX: Eliminare squadra',
    Language.pt: 'LootX: Excluir equipe',
    Language.ko: 'LootX: 팀 삭제',
    Language.cn: 'LootX: 删除团队'
})

EMAIL_DELETE_TEAM_BODY = MappingProxyType({
    Language.en: (
        'To confirm team deletion, visit '
        'http://localhost:8000/team/delete/{}\n'
        'Use the link within 5 minutes.'
    ),
    Language.ru: (
        'Для подтверждения удаления команды перейдите по ссылке '
        'http://localhost:8000/team/delete/{}\n'
        'Перейдите по ссылке в течении 5 минут.'
    ),
    Language.de: (
        'Um das Löschen des Teams zu bestätigen, besuchen Sie '
        'http://localhost:8000/team/delete/{}\n'
        'Nutzen Sie den Link innerhalb von 5 Minuten.'
    ),
    Language.es: (
        'Para confirmar la eliminación del equipo, visite '
        'http://localhost:8000/team/delete/{}\n'
        'Use el enlace en 5 minutos.'
    ),
    Language.fr: (
        'Pour confirmer la suppression de l’équipe, visitez '
        'http://localhost:8000/team/delete/{}\n'
        'Utilisez le lien dans les 5 minutes.'
    ),
    Language.it: (
        'Per confermare l’eliminazione della squadra, visita '
        'http://localhost:8000/team/delete/{}\n'
        'Usa il link entro 5 minuti.'
    ),
    Language.pt: (
        'Para confirmar a exclusão da equipe, visite '
        'http://localhost:8000/team/delete/{}\n'
        'Use o link em 5 minutos.'
    ),
    Language.ko: (
        '팀 삭제를 확인하려면 '
        'http://localhost:8000/team/delete/{} 에 방문하세요.\n'
        '5분 이내에 링크를 사용하세요.'
    ),
    Language.cn: (
        '要确认删除团队，请访问 '
        'http://localhost:8000/team/delete/{}\n'
        '请在 5 分钟内使用该链接。'
    ),
})
