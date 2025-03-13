from pydantic import Field

from app.config import AuthConfig
from app.handlers.abc.dto import BaseDTO
from app.types import UserId


class RequestChangePasswordDTO(BaseDTO):
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)


class ResponseUserDTO(BaseDTO):
    id: UserId
    username: str
    email: str
    is_active: bool
    password: str
