# flake8-in-file-ignores: noqa: WPS204, WPS203

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Literal, NoReturn, Sequence

from sqlalchemy import case, delete, select, exists
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import joinedload, selectinload

from app.db.abc.base import BaseAsyncDB, get_id
from app.db.abc.models import (QueueProtocol, RaiderProtocol, TeamProtocol,
                               UserProtocol, WoWItemProtocol, LogProtocol)
from app.db.enums import EnumAddons, EnumClasses, EnumLanguages
from app.db.exc import (ActivateUserError, DatabaseError,
                        InvalidCredentialsError, WoWItemNotFoundError,
                        RaiderNotFoundError, RaiderNotUnique,
                        TeamsNotExistsError, UniqueEmailError,
                        UniqueTeamNameError, UniqueUsernameError,
                        UserNotFoundError)
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
from app.db.sqlalchemy.models import Base, Queue, Raider, Team, User, WoWItem, Log
from app.db.wow_api.base import BaseAsyncWoWAPI, WoWAPIItem
from app.types import RaiderId, Sentinel, TeamId, UserId, Username, WoWItemId


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
                raise DatabaseError from e

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

        except DatabaseError as e:
            if isinstance(e.__cause__, IntegrityError):
                self._raise_user_unique_error(e.__cause__)
            else:
                raise e

        return new_user  # type: ignore

    async def get_user(self, id: UserId) -> UserProtocol:
        async with self.get_read_session() as session:
            user = await session.get(User, id)
            if not user:
                raise UserNotFoundError(f'User with id {id} is not found')
            return user  # type: ignore

    async def get_user_by_username(self, username: Username) -> UserProtocol:
        async with self.get_read_session() as session:
            stmt = select(User).where(User.username == username)
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f'User with username {username} is not found')
            return user  # type: ignore

    async def get_user_email(self, id: UserId) -> str:
        async with self.get_read_session() as session:
            stmt = select(User.email).where(User.id == id)
            email = (await session.execute(stmt)).scalar_one_or_none()
            if not email:
                raise UserNotFoundError(f'User with id {id} is not found')
            return email

    async def del_user(self, id: UserId) -> None:
        async with self.get_write_session() as session:
            await session.execute(delete(User).where(User.id == id))

    async def change_user_password(self, id: UserId, new_password: str) -> None:
        async with self.get_write_session() as session:
            user = await session.get(User, id)
            if user:
                user.password = new_password
                session.add(user)
            else:
                raise UserNotFoundError(f'User with id {id} is not found')

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
                if user.is_active:
                    raise ActivateUserError(f'User with username {username} is active')
                user.is_active = True
                return user.id
            else:
                raise ValueError(f"User with username {username} does not exist")

    async def create_team(
        self, name: str, addon: EnumAddons, owner_id: str, password: str,
        id: TeamId = Sentinel, vip_end: datetime | None = None,
        is_vip: bool | None = None
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

            except DatabaseError as e:
                if isinstance(e.__cause__, IntegrityError):
                    raise UniqueTeamNameError(
                        'Team with that name already exists'
                    ) from e
                else:
                    raise e

        return team  # type: ignore

    async def del_team(self, id: TeamId) -> None:
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

    async def get_team(self, id: TeamId) -> TeamProtocol:
        async with self.get_read_session() as session:
            team = await session.get(Team, id)
            if team:
                return team  # type: ignore
            else:
                raise TeamsNotExistsError(f"Team with id {id} does not exist")

    async def update_team(
        self, id: TeamId, name: str | None = None, addon: EnumAddons | None = None,
        is_vip: bool | None = None, vip_end: datetime | None = None,
        password: str | None = None, owner_id: str | None = None
    ) -> TeamProtocol:
        team = await self.get_team(id=id)
        async with self.get_write_session() as session:
            if name: team.name = name  # noqa: WPS220
            if addon: team.addon = addon  # noqa: WPS220
            if is_vip: team.is_vip = is_vip  # noqa: WPS220
            if vip_end: team.vip_end = vip_end  # noqa: WPS220
            if owner_id: team.owner_id = owner_id  # noqa: WPS220
            if password: team.password = password  # noqa: WPS220
            session.add(team)
            return team  # type: ignore

    async def get_team_by_name_with_owner(self, team_name: str) -> TeamProtocol:
        async with self.get_read_session() as session:
            stmt = (
                select(Team)
                .options(joinedload(Team.owner))
                .where(Team.name == team_name)
            )
            team = (await session.execute(stmt)).scalar_one_or_none()
            if not team:
                raise TeamsNotExistsError(
                    f"Team with name {team_name} does not exist"
                )
            return team  # type: ignore

    async def get_team_with_owner(self, team_id: TeamId) -> TeamProtocol:
        async with self.get_read_session() as session:
            stmt = (
                select(Team)
                .options(joinedload(Team.owner))
                .where(Team.id == team_id)
            )
            team = (await session.execute(stmt)).scalar_one_or_none()
            if not team:
                raise TeamsNotExistsError(
                    f"Team with id {team_id} does not exist"
                )
            return team  # type: ignore

    async def get_team_owner(self, team_id: TeamId) -> UserProtocol:
        async with self.get_read_session() as session:
            stmt = (
                select(User)
                .join(Team, Team.owner_id == User.id)
                .where(Team.id == team_id)
            )
            owner = (await session.execute(stmt)).scalar_one_or_none()
            if not owner:
                raise TeamsNotExistsError(
                    f"Owner for team with id {team_id} does not exist"
                )
            return owner  # type: ignore

    async def verify_username_password(
        self, username: Username, password: str
    ) -> UserId:
        async with self.get_read_session() as session:
            stmt = (
                select(User)
                .where(
                    User.username == username,
                    User.is_active
                )
            )
            user = (await session.execute(stmt)).scalar_one_or_none()
            if user and user.check_password(password):
                return user.id
            else:
                raise InvalidCredentialsError('Invalid username or password')

    async def get_raider(self, id: RaiderId) -> RaiderProtocol:
        async with self.get_read_session() as session:
            raider = await session.get(Raider, id)
            if raider:
                return raider  # type: ignore
            else:
                raise RaiderNotFoundError(f"Raider with id {id} does not exist")

    async def create_raider(
        self, name: str, team_id: TeamId, class_name: EnumClasses,
        is_active: bool = True, id: RaiderId = Sentinel
    ) -> RaiderProtocol:
        async with self.get_write_session() as session:
            stmt = (
                select(Raider.id)
                .where(
                    Raider.is_active,
                    Raider.team_id == team_id,
                    Raider.name == name,
                    Raider.class_name == class_name
                )
            )
            existing_raider = (await session.execute(stmt)).first()
            if existing_raider:
                raise RaiderNotUnique(
                    'Active raider with the same name or class already exists'
                    f'in the team ({existing_raider})'
                )

            raider = Raider(
                id=get_id() if id is Sentinel else id,
                name=name,
                team_id=team_id,
                class_name=class_name,
                is_active=is_active
            )
            session.add(raider)
            return raider  # type: ignore

    async def set_raider_inactive(self, id: RaiderId) -> None:
        raider = await self.get_raider(id)
        async with self.get_write_session() as session:
            raider.is_active = False
            session.add(raider)

    async def get_wow_item(self, id: WoWItemId) -> WoWItemProtocol:
        async with self.get_read_session() as session:
            wow_item = await session.get(WoWItem, id)
            if wow_item:
                return wow_item  # type: ignore
            else:
                raise WoWItemNotFoundError(f"Item with id {id} does not exist")

    async def get_wow_item_by_wow_id(
        self, wow_id: int, addon: EnumAddons, lang: EnumLanguages,
        wow_api: BaseAsyncWoWAPI
    ) -> WoWItemProtocol | None:
        use_wow_api = False

        async with self.get_read_session() as session:
            stmt = select(WoWItem).where(
                WoWItem.wow_id == wow_id,
                WoWItem.addon == addon,
                WoWItem.lang == lang
            )
            wow_item = (await session.execute(stmt)).scalar_one_or_none()

        if not wow_item:
            wow_item = self._wowapi_item_to_wow_item(
                await wow_api.get_item(
                    id=wow_id,
                    addon=addon,
                    lang=lang
                )
            )
            use_wow_api = True

        if use_wow_api and wow_item:
            async with self.get_write_session() as session:
                session.add(wow_item)

        return wow_item  # type: ignore

    async def get_queue(
        self, team_id: TeamId, wow_item_id: int
    ) -> Sequence[QueueProtocol]:
        async with self.get_read_session() as session:
            stmt = (
                select(Queue)
                .options(joinedload(Queue.raider))
                .where(
                    Queue.team_id == team_id,
                    Queue.wow_item_id == wow_item_id
                )
            )
            queues = (await session.execute(stmt)).scalars().all()
            return queues  # type: ignore

    async def create_queue(
        self, team_id: TeamId, wow_item_id: int, addon: EnumAddons,
        lang: EnumLanguages, raiders: Sequence[RaiderId],
        wow_api: BaseAsyncWoWAPI
    ) -> Sequence[QueueProtocol]:
        wow_item = await self.get_wow_item_by_wow_id(
            wow_id=wow_item_id,
            addon=addon,
            lang=lang,
            wow_api=wow_api
        )
        if not wow_item:
            raise WoWItemNotFoundError(f"Item with id {wow_item_id} does not exist")

        await self.del_queue(team_id, wow_item_id)
        try:
            async with self.get_write_session() as session:
                for i, raider_id in enumerate(raiders, start=1):
                    queue = Queue(
                        position=i,
                        team_id=team_id,
                        raider_id=raider_id,
                        wow_item_id=wow_item_id
                    )
                    session.add(queue)
        except DatabaseError as e:
            if isinstance(e.__cause__, IntegrityError):
                raise RaiderNotFoundError('Raiders not exists') from e
            else:
                raise e

        return await self.get_queue(team_id, wow_item_id)

    async def del_queue(self, team_id: TeamId, wow_item_id: int) -> None:
        async with self.get_write_session() as session:
            await session.execute(
                delete(Queue).where(
                    Queue.team_id == team_id,
                    Queue.wow_item_id == wow_item_id
                )
            )

    async def is_queue_exists(self, team_id: TeamId, wow_item_id: int) -> bool:
        async with self.get_read_session() as session:
            return bool(await session.scalar(
                select(
                    exists()
                    .where(
                        Queue.team_id == team_id,
                        Queue.wow_item_id == wow_item_id
                    )
                )
            ))

    async def create_log(
        self, team_id: TeamId, user_id: UserId, wow_item_id: int, queue: str
    ) -> LogProtocol:
        async with self.get_write_session() as session:
            log = Log(
                team_id=team_id,
                user_id=user_id,
                wow_item_id=wow_item_id,
                queue=queue
            )
            session.add(log)
        return log  # type: ignore

    async def get_logs(
        self, team_id: TeamId, wow_item_id: int | None = None,
        limit: int | None = None, offset: int | None = None
    ) -> Sequence[LogProtocol]:
        async with self.get_read_session() as session:
            stmt = (
                select(Log)
                .where(
                    Log.team_id == team_id,
                )
                .order_by(Log.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            if wow_item_id:
                stmt.where(Log.wow_item_id == wow_item_id)
            logs = (await session.execute(stmt)).scalars().all()
        return logs  # type: ignore

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

    def _wowapi_item_to_wow_item(
        self, wow_api_item: WoWAPIItem | None
    ) -> WoWItem | None:
        if not wow_api_item:
            return None
        return WoWItem(
            wow_id=wow_api_item.wow_id,
            addon=wow_api_item.addon,
            lang=wow_api_item.lang,
            html_tooltip=wow_api_item.html_tooltip,
            icon_url=wow_api_item.icon_url,
            origin_link=wow_api_item.origin_link
        )
