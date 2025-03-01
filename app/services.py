from datetime import UTC, datetime, timedelta

from app.config import Token, TokenConfigType
from app.db.abc.base import BaseAsyncDB
from app.db.exc import DatabaseError, UniqueEmailError, UniqueUsernameError
from app.task_managers.base import BaseAsyncTaskManager, TaskManagerError
from app.tokens.payloads import RegistrationTokenPayload
from app.types import RegistrationToken, Username


class AuthService:

    @staticmethod
    async def check_user_uniqueness(db: BaseAsyncDB, username: str, email: str
                                    ) -> None:
        try:
            await db.is_user_username_email_unique(username, email)
        except (UniqueUsernameError, UniqueEmailError) as e:
            raise e
        except Exception as e:
            raise DatabaseError from e

    @staticmethod
    def get_registration_token(token_type: type[Token], token_config: TokenConfigType,
                               token_exp: timedelta, username: Username
                               ) -> RegistrationToken:
        registration_token_payload = RegistrationTokenPayload(
            sub=username,
            exp=int((datetime.now(UTC) + token_exp).timestamp()),
        )
        return token_type(
            registration_token_payload,
            token_config
        ).encode()

    @staticmethod
    async def registation(db: BaseAsyncDB, username: str, email: str,
                          password: str, task_manager: BaseAsyncTaskManager,
                          del_inactive_user_after: timedelta
                          ) -> None:
        try:
            registration_user = await db.create_user(
                username=username,
                password=password,
                email=email,
                is_active=False
            )
        except Exception as e:
            raise DatabaseError from e

        try:
            await task_manager.del_inactive_user(
                user_id=registration_user.id,
                eta_delta=del_inactive_user_after
            )
        except Exception as e:
            await db.del_user(registration_user.id)
            raise TaskManagerError from e
