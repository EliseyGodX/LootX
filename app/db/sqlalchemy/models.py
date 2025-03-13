# flake8-in-file-ignores: noqa: WPS432, WPS202, WPS226, WPS110

from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.db.abc.base import get_id
from app.db.enums import EnumAddons, EnumClasses
from app.types import ItemId, LogId, QueueId, RaiderId, TeamId, UserId

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class PasswordHashingError(Exception): ...


class Base(DeclarativeBase):
    pass


class ModelWithPassword(Base):
    __abstract__ = True

    _password: Mapped[str] = mapped_column(
        String(64), nullable=False, name='password'
    )

    def __init__(self, is_password_hash_check_enabled: bool = True, **kwargs) -> None:
        self.is_password_hash_check_enabled = is_password_hash_check_enabled
        password = kwargs.pop('password', None)
        if password:
            self.password = password
        super().__init__(**kwargs)

    @hybrid_property
    def password(self) -> str:  # type: ignore[reportRedeclaration]
        return self._password

    @password.expression  # type: ignore[reportRedeclaration]
    def password(cls) -> str:  # type: ignore[reportRedeclaration]  # noqa: B902
        return cls._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = pwd_context.hash(value)  # noqa: WPS60

    def is_password_hashed(self) -> bool:
        return pwd_context.identify(self._password) is not None

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self._password)


class User(ModelWithPassword):
    __tablename__ = 'users'

    id: Mapped[UserId] = mapped_column(String, primary_key=True, default=get_id)
    username: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    teams: Mapped[list['Team']] = relationship(back_populates='owner')
    logs: Mapped[list['Log']] = relationship(back_populates='user')


class Team(ModelWithPassword):
    __tablename__ = 'teams'

    id: Mapped[TeamId] = mapped_column(String, primary_key=True, default=get_id)
    name: Mapped[str] = mapped_column(
        String(24), unique=True, nullable=False, index=True
    )
    addon: Mapped[EnumAddons] = mapped_column(
        SAEnum(EnumAddons, name='addons'), nullable=False
    )
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vip_end: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    owner_id: Mapped[UserId] = mapped_column(ForeignKey('users.id'), nullable=False)
    owner: Mapped['User'] = relationship(back_populates='teams')
    raiders: Mapped[list['Raider']] = relationship(back_populates='team')
    logs: Mapped[list['Log']] = relationship(back_populates='team')
    queues: Mapped[list['Queue']] = relationship(back_populates='team')


class Raider(Base):
    __tablename__ = 'raiders'

    id: Mapped[RaiderId] = mapped_column(String, primary_key=True, default=get_id)
    name: Mapped[str] = mapped_column(String(12), nullable=False)
    team_id: Mapped[TeamId] = mapped_column(ForeignKey('teams.id'), nullable=False)
    class_name: Mapped[EnumClasses] = mapped_column(
        SAEnum(EnumClasses, name='classes'), nullable=False
    )
    team: Mapped['Team'] = relationship(back_populates='raiders')
    queues: Mapped[list['Queue']] = relationship(back_populates='raider')


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[ItemId] = mapped_column(String, primary_key=True, default=get_id)
    wow_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    addon: Mapped[EnumAddons] = mapped_column(
        SAEnum(EnumAddons, name='addons'), nullable=False
    )
    html_tooltip: Mapped[str] = mapped_column(String, nullable=False)
    icon_id: Mapped[str] = mapped_column(String, nullable=False)
    logs: Mapped[list['Log']] = relationship(back_populates='item')
    queues: Mapped[list['Queue']] = relationship(back_populates='item')


class Queue(Base):
    __tablename__ = 'queues'

    id: Mapped[QueueId] = mapped_column(String, primary_key=True, default=get_id)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[TeamId] = mapped_column(ForeignKey('teams.id'), nullable=False)
    raider_id: Mapped[RaiderId] = mapped_column(
        ForeignKey('raiders.id'), nullable=False
    )
    item_id: Mapped[ItemId] = mapped_column(ForeignKey('items.id'), nullable=False)
    team: Mapped['Team'] = relationship(back_populates='queues')
    raider: Mapped['Raider'] = relationship(back_populates='queues')
    item: Mapped['Item'] = relationship(back_populates='queues')


class Log(Base):
    __tablename__ = 'logs'

    id: Mapped[LogId] = mapped_column(String, primary_key=True, default=get_id)
    team_id: Mapped[TeamId] = mapped_column(ForeignKey('teams.id'), nullable=False)
    user_id: Mapped[UserId] = mapped_column(ForeignKey('users.id'), nullable=False)
    item_id: Mapped[ItemId] = mapped_column(ForeignKey('items.id'), nullable=False)
    data: Mapped[str] = mapped_column(String)
    team: Mapped['Team'] = relationship(back_populates='logs')
    user: Mapped['User'] = relationship(back_populates='logs')
    item: Mapped['Item'] = relationship(back_populates='logs')
