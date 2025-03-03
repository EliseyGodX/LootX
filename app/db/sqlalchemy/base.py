from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, NoReturn, Sequence

from sqlalchemy import case, delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.db.abc.base import BaseAsyncDB
from app.db.exc import ActivateUserError, UniqueEmailError, UniqueUsernameError
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
from app.db.sqlalchemy.models import Base, User, ulid
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

    async def create_user(self, username: str, password: str,  # type: ignore
                          email: str, is_active: bool,
                          id: UserId = Sentinel) -> User:
        try:
            async with self.get_write_session() as session:
                new_user = User(
                    id=ulid() if id is Sentinel else id,
                    username=username,
                    email=email,
                    is_active=is_active,
                    password=password
                )
                session.add(new_user)
                return new_user

        except IntegrityError as e:
            self._raise_user_unique_error(e)

    async def del_user(self, id: UserId) -> None:
        async with self.get_write_session() as session:
            await session.execute(delete(User).where(User.id == id))

    async def is_user_username_email_unique(self, username: str, email: str
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
