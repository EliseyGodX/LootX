import asyncpg
from sqlalchemy.exc import IntegrityError

from app.db.base import get_session
from app.db.models import User, ulid
from app.types import Sentinel


async def create_user(username: str, password: str,
                      email: str, is_active: bool,
                      id: str = Sentinel) -> User:
    id = id if id else ulid()
    async with get_session() as session:
        new_user = User(
            id=id,
            username=username,
            email=email,
            is_active=is_active
        ).set_password(password)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
