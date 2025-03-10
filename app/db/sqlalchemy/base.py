from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Literal, NoReturn, Sequence

from sqlalchemy import case, delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import selectinload

from app.db.abc.base import BaseAsyncDB, get_id
from app.db.abc.models import TeamProtocol, UserProtocol
from app.db.enums import EnumAddons
from app.db.exc import (ActivateUserError, InvalidCredentialsError,
                        TeamsNotExistsError, UniqueEmailError,
                        UniqueTeamNameError, UniqueUsernameError,
                        UserNotFoundError)
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
from app.db.sqlalchemy.models import Base, Team, User
from app.types import Sentinel, UserId, Username


class DatabaseWriteError(Exception): ...


@dataclass
class AsyncSQLAlchemyDB(BaseAsyncDB[SQLAlchemyDBConfig]):

    async def connect(self) -> None:
        self.engine = create_async_engine(
            url=self.config.db_url,
            **self.config.engine_kwargs
        )
        self.sessionmaker = async_sessionmaker(
            bind=self.engine,
            **self.config.session_maker_kwargs
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_read_session(self) -> AsyncGenerator[AsyncSession, None]:
        def prevent_modifications(*args, **kwargs) -> NoReturn:  # noqa: ANN002
            raise DatabaseWriteError(
                'Modifications are not allowed in read-only session'
            )
        async with self.sessionmaker() as session:
            session: AsyncSession
            session.flush = prevent_modifications
            yield session

    @asynccontextmanager
    async def get_write_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.sessionmaker() as session:
            session: AsyncSession
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e

    async def create_user(
        self, username: str, password: str, email: str, is_active: bool,
        id: UserId = Sentinel
    ) -> UserProtocol:
        try:
            async with self.get_write_session() as session:
                new_user = User(
                    id=get_id() if id is Sentinel else id,
                    username=username,
                    email=email,
                    is_active=is_active,
                    password=password
                )
                session.add(new_user)
                return new_user  # type: ignore

        except IntegrityError as e:
            self._raise_user_unique_error(e)

    async def get_user(self, id: UserId) -> UserProtocol:
        async with self.get_read_session() as session:
            user = await session.get(User, id)
            if not user:
                raise UserNotFoundError('User is not found')
            return user  # type: ignore

    async def del_user(self, id: UserId) -> None:
        async with self.get_write_session() as session:
            await session.execute(delete(User).where(User.id == id))

    async def is_user_username_email_unique(
        self, username: str, email: str
    ) -> Literal[True]:
        async with self.get_read_session() as session:
            stmt = (
                select(
                    case(
                        (User.email == email, 'email'),
                        (User.username == username, 'username')
                    )
                )
                .where((User.email == email) | (User.username == username))
            )
            non_unique_fields = (await session.execute(stmt)).scalars().all()

        if len(non_unique_fields) == 0:
            return True
        else:
            self._raise_user_unique_error(non_unique_fields)

    async def is_user_active(self, id: UserId) -> bool:
        async with self.get_read_session() as session:
            user = await session.get(User, id)
            if user:
                return user.is_active
            else:
                raise ValueError(f"User with id {id} does not exist")

    async def activate_user(self, username: Username) -> UserId:
        async with self.get_write_session() as session:
            query_result = await session.execute(
                select(User).where(User.username == username)
            )
            user = query_result.scalar_one_or_none()
            if user:
                if not user.is_active:
                    raise ActivateUserError(f'User with username {username} is active')
                user.is_active = True
                return user.id
            else:
                raise ValueError(f"User with username {username} does not exist")

    async def create_team(
        self, name: str, addon: EnumAddons, owner_id: str, password: str,
        id: str = Sentinel, vip_end: datetime | None = None, is_vip: bool | None = None
    ) -> TeamProtocol:
        async with self.get_write_session() as session:
            try:
                team = Team(
                    id=get_id() if id is Sentinel else id,
                    name=name,
                    addon=addon,
                    is_vip=is_vip,
                    vip_end=vip_end,
                    owner_id=owner_id,
                    password=password
                )
                session.add(team)
                return team  # type: ignore

            except IntegrityError as e:
                raise UniqueTeamNameError(
                    'Team with that name already exists'
                ) from e

    async def del_team(self, id: str) -> None:
        async with self.get_write_session() as session:
            try:
                team = await self.get_team(id=id)
                await session.delete(team)
            except IntegrityError as e:
                raise TeamsNotExistsError(f"Teams with '{id}' does not exists") from e

    async def get_team_by_name(self, name: str) -> TeamProtocol:
        async with self.get_read_session() as session:
            team = (await session.execute(
                select(Team)
                .options(selectinload(Team.owner))
                .filter(Team.name == name)
            )).scalar_one_or_none()
            if team:
                return team  # type: ignore
            else:
                raise TeamsNotExistsError(f"Team with name {name} does not exist")

    async def get_team(self, id: str) -> TeamProtocol:
        async with self.get_read_session() as session:
            team = await session.get(Team, id)
            if team:
                return team  # type: ignore
            else:
                raise TeamsNotExistsError(f"Team with id {id} does not exist")

    async def update_team(
        self, id: str, name: str = Sentinel, addon: EnumAddons = Sentinel,
        is_vip: bool = Sentinel, vip_end: datetime = Sentinel, password: str = Sentinel,
        owner_id: str = Sentinel
    ) -> TeamProtocol:
        team = await self.get_team(id=id)
        async with self.get_write_session() as session:
            if name is not Sentinel: team.name = name  # noqa: WPS220
            if addon is not Sentinel: team.addon = addon  # noqa: WPS220
            if is_vip is not Sentinel: team.is_vip = is_vip  # noqa: WPS220
            if vip_end is not Sentinel: team.vip_end = vip_end  # noqa: WPS220
            if owner_id is not Sentinel: team.owner_id = owner_id  # noqa: WPS220
            if password is not Sentinel: team.password = password  # noqa: WPS220
            session.add(team)
            return team  # type: ignore

    async def verify_username_password(
        self, username: Username, password: str
    ) -> UserId:
        async with self.get_read_session() as session:
            stmt = (
                select(User)
                .where(
                    User.username == username
                )
            )
            user = (await session.execute(stmt)).scalar_one_or_none()
            if user and user.check_password(password):
                return user.id
            else:
                raise InvalidCredentialsError("Invalid username or password")

    async def close(self) -> None:
        await self.engine.dispose()

    def _raise_user_unique_error(self, e: IntegrityError | Sequence) -> NoReturn:
        if isinstance(e, IntegrityError):
            constraint: str = getattr(e.orig, 'constraint_name')  # noqa: B009
            if constraint == 'username':
                raise UniqueUsernameError('Username is already taken') from e
            if constraint == 'email':
                raise UniqueEmailError('Email is already registered') from e
            raise e

        elif isinstance(e, Sequence):
            if 'username' in e:
                raise UniqueUsernameError('Username is already taken')
            if 'email' in e:
                raise UniqueEmailError('Email is already registered')
            raise ValueError('Error raised due to unknown fields in the sequence')

        raise ValueError('Argument e of unsupported type')
