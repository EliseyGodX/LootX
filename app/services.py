from datetime import UTC, datetime, timedelta

import jwt

from app.db.base import DatabaseError
from app.db.crud import (UniqueEmailError, UniqueUsernameError, create_user,
                         is_user_username_email_unique)
from app.tokens import RegistrationTokenPayload
from app.types import RegistrationToken, Username


class AuthService:

    @staticmethod
    async def check_user_uniqueness(username: str, email: str) -> None:
        try:
            await is_user_username_email_unique(username, email)
        except (UniqueUsernameError, UniqueEmailError) as e:
            raise e
        except Exception as e:
            raise DatabaseError from e

    @staticmethod
    def get_registration_token(username: Username, jwt_algorithm: str,
                               jwt_key: str, token_exp: timedelta
                               ) -> RegistrationToken:
        registration_token_payload = RegistrationTokenPayload(
            sub=username,
            exp=int((datetime.now(UTC) + token_exp).timestamp()),
        )
        return jwt.encode(
            registration_token_payload.model_dump(),
            algorithm=jwt_algorithm,
            key=jwt_key
        )

    @staticmethod
    async def registation(username: str, email: str,
                          password: str) -> None:
        try:
            await create_user(
                username=username,
                password=password,
                email=email,
                is_active=False
            )
        except Exception as e:
            raise DatabaseError from e
