from pydantic import BaseModel, Field

from app.config import AuthConfig
from app.types import AccessToken, RefreshToken


class RequestRegistrationDTO(BaseModel):
    username: str = Field(..., min_length=AuthConfig.username_min_length,
                          max_length=AuthConfig.username_max_length)
    email: str = Field(..., max_length=AuthConfig.email_max_length)
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)


class ResponseAccessRefreshTokensDTO(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class RequestAuthDTO(BaseModel):
    username: str = Field(..., min_length=AuthConfig.username_min_length,
                          max_length=AuthConfig.username_max_length)
    password: str = Field(..., min_length=AuthConfig.password_min_length,
                          max_length=AuthConfig.password_max_length)
