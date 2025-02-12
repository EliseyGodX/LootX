import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, NoReturn

from app.config import DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError


engine = create_async_engine(DATABASE_URL, echo=True, future=True)
Base = declarative_base()

async_session = sessionmaker(
    bind=engine,  # type: ignore[reportArgumentType]
    class_=AsyncSession,
    expire_on_commit=False
)


class DatabaseError(Exception): ...
class DatabaseWriteError(DatabaseError): ...


@asynccontextmanager
async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    def prevent_modifications(*args, **kwargs) -> NoReturn:  # noqa: ANN002
        raise DatabaseWriteError("Modifications are not allowed in read-only session")

    async with async_session() as session:  # type: ignore[reportGeneralTypeIssues]
        session: AsyncSession
        session.flush = prevent_modifications
        yield session


@asynccontextmanager
async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:  # type: ignore[reportGeneralTypeIssues]
        session: AsyncSession
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e


def _db_init():
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.create_task(create_tables())
    else:
        loop.run_until_complete(create_tables())
