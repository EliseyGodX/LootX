from typing import Literal, NoReturn, Sequence

from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError

from app.db.base import get_read_session, get_write_session
from app.db.models import User, ulid
from app.types import Sentinel


class UniqueUsernameError(Exception): ...
class UniqueEmailError(Exception): ...


def _raise_user_unique_error(e: IntegrityError | Sequence) -> NoReturn:
    if isinstance(e, IntegrityError):
        constraint: str = getattr(e.orig, "constraint_name")  # noqa: B009
        if constraint == "username":
            raise UniqueUsernameError("Username is already taken") from e
        if constraint == "email":
            raise UniqueEmailError("Email is already registered") from e
        raise e

    elif isinstance(e, Sequence):
        if "username" in e:
            raise UniqueUsernameError("Username is already taken")
        if "email" in e:
            raise UniqueEmailError("Email is already registered")
        raise ValueError('Error raised due to unknown fields in the sequence')

    raise ValueError('Argument e of unsupported type')


async def create_user(username: str, password: str,
                      email: str, is_active: bool,
                      id: str = Sentinel) -> User:
    try:
        async with get_write_session() as session:
            new_user = User(
                id=id if id else ulid(),
                username=username,
                email=email,
                is_active=is_active,
                password=password
            )
            session.add(new_user)
            return new_user

    except IntegrityError as e:
        _raise_user_unique_error(e)


# async def delete_user(user_id: str) -> None:
#     async with get_write_session() as session:
#         user = await session.get(User, user_id)
#         if user:
#             await session.delete(user)
#         else:
#             raise ValueError(f"User with id {user_id} does not exist")


async def is_user_username_email_unique(username: str, email: str) -> Literal[True]:
    async with get_read_session() as session:
        stmt = (
            select(
                case(
                    (User.email == email, "email"),
                    (User.username == username, "username")
                )
            )
            .where((User.email == email) | (User.username == username))
        )
        non_unique_fields = (await session.execute(stmt)).scalars().all()

    if len(non_unique_fields) == 0:
        return True
    else:
        _raise_user_unique_error(non_unique_fields)
