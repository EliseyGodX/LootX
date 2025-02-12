from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.types import UserId, Username


class TokenType(Enum):
    access = "ACCESS"
    refresh = "REFRESH"
    registration = "REGISTRATION"


class _BaseTokenPayload(BaseModel):
    exp: int

    class Config:
        use_enum_values = True
        validate_default = True


class AccessTokenPayload(_BaseTokenPayload):
    type: Literal[TokenType.access] = TokenType.access
    sub: UserId


class RefreshTokenPayload(_BaseTokenPayload):
    type: Literal[TokenType.refresh] = TokenType.refresh
    sub: UserId


class RegistrationTokenPayload(_BaseTokenPayload):
    type: Literal[TokenType.registration] = TokenType.registration
    sub: Username
