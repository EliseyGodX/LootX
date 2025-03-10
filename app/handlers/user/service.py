from app.db.abc.base import BaseAsyncDB
from app.db.abc.models import UserProtocol
from app.db.exc import DatabaseError, UserNotFoundError
from app.types import UserId


class UserService:

    @staticmethod
    async def get_user(db: BaseAsyncDB, user_id: UserId) -> UserProtocol:
        try:
            return await db.get_user(user_id)
        except UserNotFoundError as e:
            raise e
        except Exception as e:
            raise DatabaseError from e
