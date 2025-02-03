from datetime import UTC, datetime
from typing import Literal

import jwt

from app.config import (EMAIL_REGISTRATION_MESSAGE, JWT_ALGORITHM, JWT_KEY,
                        REGISTRATION_TOKEN_EXP, )
from app.db.models import User, ulid
from app.tokens import TokenPayload, TokenType
from app.types import RegistrationToken


class AuthService:

    @staticmethod
    async def registration(username: str, email: str,
                           password: str) -> RegistrationToken:

        user_id = ulid()

        sa_user = User(
            id=user_id,
            username=username,
            email=email,
            is_active=False
        ).set_password(password)

        user_reg_token = TokenPayload[Literal[TokenType.REGISTRATION]](
            type=TokenType.REGISTRATION,
            sub=user_id,
            exp=int((datetime.now(UTC) + REGISTRATION_TOKEN_EXP).timestamp()),
        )

        return jwt.encode(
            user_reg_token.model_dump(),
            key=JWT_KEY,
            algorithm=JWT_ALGORITHM
        )
