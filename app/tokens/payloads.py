from pydantic import BaseModel
from typing import Literal
from app.types import TeamId, UserId, Username


class BaseTokenPayload(BaseModel):

    class Config:
        use_enum_values = True
        validate_default = True
        arbitrary_types_allowed = True


class AccessTokenPayload(BaseTokenPayload):
    exp: float
    sub: UserId
    type: Literal['access'] = 'access'


class RefreshTokenPayload(BaseTokenPayload):
    exp: float
    sub: UserId
    type: Literal['refresh'] = 'refresh'


class RegistrationTokenPayload(BaseTokenPayload):
    exp: float
    sub: Username
    type: Literal['registration'] = 'registration'


class ChangePasswordTokenPayload(BaseTokenPayload):
    exp: float
    sub: UserId
    type: Literal['change-password'] = 'change-password'


class DeleteTeamTokenPayload(BaseTokenPayload):
    exp: float
    sub: TeamId
    type: Literal['delete-team'] = 'delete-team'
