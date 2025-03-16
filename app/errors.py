# flake8-in-file-ignores: noqa: WPS432

from http import HTTPStatus
from typing import Any, Mapping

from litestar.exceptions import HTTPException
from litestar.openapi.datastructures import ResponseSpec
from litestar.openapi.spec import Example
from pydantic import BaseModel

from app.types import Sentinel


class BaseError(BaseModel):
    status_code: int = 400
    detail: str = ''
    extra: dict = {}


class UsernameNotUnique(BaseError):
    status_code: int = 409
    detail: str = HTTPStatus(409).phrase
    extra: dict = {
        'error_code': 1,
        'message': 'Username not unique'
    }


class EmailNotUnique(BaseError):
    status_code: int = 409
    detail: str = HTTPStatus(409).phrase
    extra: dict = {
        'error_code': 2,
        'message': 'Email not unique'
    }


class EmailNonExistent(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 3,
        'message': 'Email does not exist'
    }


class RegistrationTokenInvalid(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 4,
        'message': 'Registration token is invalid'
    }


class AccessTokenInvalid(BaseError):
    status_code: int = 401
    detail: str = HTTPStatus(401).phrase
    extra: dict = {
        'error_code': 5,
        'message': 'Access token is invalid'
    }


class RefreshTokenInvalid(BaseError):
    status_code: int = 401
    detail: str = HTTPStatus(401).phrase
    extra: dict = {
        'error_code': 6,
        'message': 'Refresh token is invalid'
    }


class UserIsActive(BaseError):
    status_code: int = 403
    detail: str = HTTPStatus(403).phrase
    extra: dict = {
        'error_code': 7,
        'message': 'The user is already active'
    }


class TeamNameNotUnique(BaseError):
    status_code: int = 409
    detail: str = HTTPStatus(409).phrase
    extra: dict = {
        'error_code': 8,
        'message': 'The team name is already active'
    }


class TeamNotExists(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 9,
        'message': 'The team does not exist'
    }


class UserNotExists(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 10,
        'message': 'User not exists'
    }


class InvalidCredentials(BaseError):
    status_code: int = 401
    detail: str = HTTPStatus(401).phrase
    extra: dict = {
        'error_code': 11,
        'message': 'Invalid credentials'
    }


class AuthorizationHeaderMissing(BaseError):
    status_code: int = 401
    detail: str = HTTPStatus(401).phrase
    extra: dict = {
        'error_code': 13,
        'message': 'Authorization header missing'
    }


class RefreshTokenCookieMissing(BaseError):
    status_code: int = 401
    detail: str = HTTPStatus(401).phrase
    extra: dict = {
        'error_code': 14,
        'message': 'Refresh token missing in cookie'
    }


class UpdateTokens(BaseError):
    status_code: int = 401
    detail: str = HTTPStatus(401).phrase
    extra: dict = {
        'error_code': 15,
        'message': 'New access and refresh tokens'
    }


class ChangePasswordTokenInvalid(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 16,
        'message': 'Change password token is invalid'
    }


class DeleteTeamTokenInvalid(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 17,
        'message': 'Delete team token is invalid'
    }


class UserNotTeamOwner(BaseError):
    status_code: int = 403
    detail: str = HTTPStatus(403).phrase
    extra: dict = {
        'error_code': 18,
        'message': 'The action is available only to the owner of the team'
    }


class TokensSubjectNotEqual(BaseError):
    status_code: int = 403
    detail: str = HTTPStatus(403).phrase
    extra: dict = {
        'error_code': 19,
        'message': 'Tokens subject not equal'
    }


class RaiderNotExists(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 20,
        'message': 'Raider not exists'
    }


class RaiderNotUnique(BaseError):
    status_code: int = 409
    detail: str = HTTPStatus(409).phrase
    extra: dict = {
        'error_code': 21,
        'message': ('Active raider with the same name or class already exists'
                    'in the team')
    }


class ItemNotExists(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 22,
        'message': 'Item not exists'
    }


class QueueNotExists(BaseError):
    status_code: int = 422
    detail: str = HTTPStatus(422).phrase
    extra: dict = {
        'error_code': 22,
        'message': 'Queue not exists'
    }


def litestar_raise(
    error_model: type[BaseError], add_to_extra: Mapping[str, Any] = Sentinel,
    headers: dict[str, str] = Sentinel
) -> HTTPException:
    error_instance = error_model()
    return HTTPException(
        status_code=error_instance.status_code,
        detail=error_instance.detail,
        extra=({**error_instance.extra, **add_to_extra}
               if add_to_extra is not Sentinel else error_instance.extra),
        headers=headers if headers is not Sentinel else None,
    )


def litestar_response_spec(examples: list[Example]) -> ResponseSpec:
    return ResponseSpec(
        data_container=BaseError,
        description='errors',
        examples=examples
    )
