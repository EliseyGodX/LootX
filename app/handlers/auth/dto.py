from pydantic import Field

from app.config import AuthConfig
from app.handlers.abc.dto import BaseDTO


class RequestRegistrationDTO(BaseDTO):
    username: str = Field(..., min_length=AuthConfig.username_min_length,
                          max_length=AuthConfig.username_max_length)
    email: str = Field(..., max_length=AuthConfig.email_max_length)
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)


class RequestAuthDTO(BaseDTO):
    username: str = Field(..., min_length=AuthConfig.username_min_length,
                          max_length=AuthConfig.username_max_length)
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)
