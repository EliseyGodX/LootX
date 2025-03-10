from datetime import UTC, datetime, timedelta
from typing import TypeVar

from app.config import Token, TokenConfigType
from app.db.abc.base import BaseAsyncDB
from app.db.exc import (ActivateUserError, DatabaseError, UniqueEmailError,
                        UniqueUsernameError, InvalidCredentialsError)
from app.task_managers.base import BaseAsyncTaskManager, TaskManagerError
from app.tokens.base import BaseToken, DecodeTokenError, EncodeTokenError
from app.tokens.payloads import (AccessTokenPayload, RefreshTokenPayload,
                                 RegistrationTokenPayload)
from app.types import RegistrationToken, UserId, Username

TokenType = TypeVar('TokenType', bound=BaseToken)


class AuthService:

    @staticmethod
    async def check_user_uniqueness(
        db: BaseAsyncDB, username: str, email: str
    ) -> None:
        try:
            await db.is_user_username_email_unique(username, email)
        except (UniqueUsernameError, UniqueEmailError) as e:
            raise e
        except Exception as e:
            raise DatabaseError from e

    @staticmethod
    def create_registration_token(
        token_type: type[Token], token_config: TokenConfigType, token_exp: timedelta,
        sub: Username
    ) -> RegistrationToken:
        registration_token_payload = RegistrationTokenPayload(
            sub=sub,
            exp=int((datetime.now(UTC) + token_exp).timestamp()),
        )
        return token_type(
            registration_token_payload,
            token_config
        ).encode()

    @staticmethod
    async def registration(
        db: BaseAsyncDB, username: str, email: str, password: str,
        task_manager: BaseAsyncTaskManager, del_inactive_user_after: timedelta
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

    @staticmethod
    async def verify_access_token(
        token: str, token_type: type[TokenType], token_config: TokenConfigType
    ) -> TokenType:
        try:
            return token_type.decode(
                token, token_config, AccessTokenPayload
            )
        except DecodeTokenError as e:
            raise e

    @staticmethod
    async def verify_refresh_token(
        token: str, token_type: type[TokenType], token_config: TokenConfigType
    ) -> TokenType:
        try:
            return token_type.decode(
                token, token_config, RefreshTokenPayload
            )
        except DecodeTokenError as e:
            raise e

    @staticmethod
    async def verify_registration_token(
        token: str, token_type: type[TokenType], token_config: TokenConfigType
    ) -> TokenType:
        try:
            return token_type.decode(
                token, token_config, RegistrationTokenPayload
            )
        except DecodeTokenError as e:
            raise e

    @staticmethod
    async def activate_user(db: BaseAsyncDB, username: Username) -> UserId:
        try:
            return await db.activate_user(username=username)

        except ActivateUserError as e:
            raise ActivateUserError from e

        except Exception as e:
            raise DatabaseError from e

    @staticmethod
    async def create_access_token(
        token_type: type[TokenType], token_config: TokenConfigType, exp: timedelta,
        sub: UserId
    ) -> TokenType:
        try:
            return token_type(
                config=token_config,
                payload=AccessTokenPayload(
                    exp=(datetime.now() + exp).timestamp(),
                    sub=sub
                )
            )
        except EncodeTokenError as e:
            raise e

    @staticmethod
    async def create_refresh_token(
        token_type: type[TokenType], token_config: TokenConfigType, exp: timedelta,
        sub: Username
    ) -> TokenType:
        try:
            return token_type(
                config=token_config,
                payload=RefreshTokenPayload(
                    exp=(datetime.now() + exp).timestamp(),
                    sub=sub
                )
            )
        except EncodeTokenError as e:
            raise e

    @staticmethod
    async def verify_username_password(
        db: BaseAsyncDB, username: Username, password: str
    ) -> UserId:
        try:
            return await db.verify_username_password(
                username=username,
                password=password
            )
        except InvalidCredentialsError as e:
            raise e
        except Exception as e:
            raise DatabaseError from e
