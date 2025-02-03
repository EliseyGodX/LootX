# flake8-in-file-ignores: noqa: WPS432, WPS202, WPS226, WPS110

from enum import Enum

from passlib.context import CryptContext
from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ulid import ULID

from app.db.base import Base


def ulid() -> str:
    return str(ULID())


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EnumClasses(Enum):
    warrior = "warrior"
    paladin = "paladin"
    hunter = "hunter"
    rogue = "rogue"
    priest = "priest"
    shaman = "shaman"
    mage = "mage"
    warlock = "warlock"
    monk = "monk"
    druid = "druid"
    demon_hunter = "demon-hunter"
    death_knight = "death-knight"
    evoker = "evoker"


class EnumAddons(Enum):
    retail = "retail"
    classic = "classic"
    cata = "cata"
    tbc = "tbc"
    wotlk = "wotlk"


class EnumLanguage(Enum):
    ru = "ru"
    de = "de"
    en = "en"
    es = "es"
    fr = "fr"
    it = "it"
    pt = "pt"
    ko = "ko"
    cn = "cn"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    username: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, index=True
    )
    _password: Mapped[str] = mapped_column(
        String(60), nullable=False, column="password"
    )
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    teams: Mapped[list["Team"]] = relationship(back_populates="owner")
    logs: Mapped[list["Log"]] = relationship(back_populates="user")

    def __init__(self, **kwargs) -> None:
        password = kwargs.pop("password", None)
        if password:
            self.password = password
        super().__init__(**kwargs)

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = pwd_context.hash(password)  # noqa: WPS601

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self._password)

    def is_password_hashed(self) -> bool:
        return pwd_context.identify(self._password) is not None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email
        }

    @classmethod
    def from_dict(cls, **user_kwargs) -> "User":
        return cls(
            id=user_kwargs.get("id"),
            username=user_kwargs.get("username"),
            password=user_kwargs.get("password"),
            email=user_kwargs.get("email")
        )


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    name: Mapped[str] = mapped_column(
        String(24), unique=True, nullable=False, index=True
    )
    password: Mapped[str] = mapped_column(String(24), nullable=False)
    addon: Mapped[EnumAddons] = mapped_column(
        SAEnum(EnumAddons, name="addons"), nullable=False
    )
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vip_end: Mapped[DateTime | None] = mapped_column(DateTime, default=None)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship(back_populates="teams")
    raiders: Mapped[list["Raider"]] = relationship(back_populates="team")
    logs: Mapped[list["Log"]] = relationship(back_populates="team")
    queues: Mapped[list["Queue"]] = relationship(back_populates="team")


class Raider(Base):
    __tablename__ = "raiders"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    name: Mapped[str] = mapped_column(String(12), nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team: Mapped["Team"] = relationship(back_populates="raiders")
    class_name: Mapped[EnumClasses] = mapped_column(
        SAEnum(EnumClasses, name="classes"), nullable=False
    )
    queues: Mapped[list["Queue"]] = relationship(back_populates="raider")


class Item(Base):
    __tablename__ = "items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    wow_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    html_tooltip: Mapped[str] = mapped_column(String, nullable=False)
    icon_id: Mapped[str] = mapped_column(String, nullable=False)
    logs: Mapped[list["Log"]] = relationship(back_populates="item")
    queues: Mapped[list["Queue"]] = relationship(back_populates="item")


class Queue(Base):
    __tablename__ = "queues"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team: Mapped["Team"] = relationship(back_populates="queues")
    raider_id: Mapped[str] = mapped_column(ForeignKey("raiders.id"), nullable=False)
    raider: Mapped["Raider"] = relationship(back_populates="queues")
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    item: Mapped["Item"] = relationship(back_populates="queues")


class Log(Base):
    __tablename__ = "logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team: Mapped["Team"] = relationship(back_populates="logs")
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="logs")
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    item: Mapped["Item"] = relationship(back_populates="logs")
    sequence: Mapped[str] = mapped_column(String)
