from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.types import UserId, Username


class TokenType(Enum):
    access = 'ACCESS'
    refresh = 'REFRESH'
    registration = 'REGISTRATION'


class BaseTokenPayload(BaseModel):

    class Config:
        use_enum_values = True
        validate_default = True
        arbitrary_types_allowed = True


class AccessTokenPayload(BaseTokenPayload):
    exp: int
    type: Literal[TokenType.access] = TokenType.access
    sub: UserId


class RefreshTokenPayload(BaseTokenPayload):
    exp: int
    type: Literal[TokenType.refresh] = TokenType.refresh
    sub: UserId


class RegistrationTokenPayload(BaseTokenPayload):
    exp: int
    type: Literal[TokenType.registration] = TokenType.registration
    sub: Username
