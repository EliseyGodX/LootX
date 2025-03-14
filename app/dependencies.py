# flake8-in-file-ignores: noqa: B904

from litestar.connection import Request

from app import errors as error
from app.config import AuthConfig, Language
from app.errors import litestar_raise
from app.tokens.base import (BaseToken, BaseTokenConfig, DecodeTokenError,
                             TokenExpiredError, create_access_token,
                             create_refresh_token)
from app.tokens.payloads import AccessTokenPayload, RefreshTokenPayload


def get_language(request: Request) -> Language:
    lang = request.cookies.get('language', Language.en.value)
    try:
        lang = Language(lang)
    except ValueError:
        lang = Language.en
    return lang


def auth_client(
    request: Request, token_type: type[BaseToken], token_config: BaseTokenConfig
) -> AccessTokenPayload:
    is_access_token_expired = None

    try:
        access_token = token_type.decode(
            token=request.headers['Authorization'].split(" ", 1)[1],
            config=token_config,
            payload_type=AccessTokenPayload
        )

    except TokenExpiredError:
        is_access_token_expired = True

    except (DecodeTokenError, IndexError):
        raise litestar_raise(error.AccessTokenInvalid)

    except KeyError:
        raise litestar_raise(error.AuthorizationHeaderMissing)

    if not is_access_token_expired:
        return access_token.payload  # type: ignore

    try:
        refresh_token = token_type.decode(
            token=request.cookies['refresh-token'],
            config=token_config,
            payload_type=RefreshTokenPayload
        )
        refresh_token_payload: RefreshTokenPayload = (
            refresh_token.payload
        )  # type: ignore

    except DecodeTokenError:
        raise litestar_raise(error.RefreshTokenInvalid)

    except KeyError:
        raise litestar_raise(error.RefreshTokenCookieMissing)

    new_access_token = create_access_token(
        token_type=token_type,
        token_config=token_config,
        exp=AuthConfig.access_token_exp,
        sub=refresh_token_payload.sub
    )

    new_refresh_token = create_refresh_token(
        token_type=token_type,
        token_config=token_config,
        exp=AuthConfig.access_token_exp,
        sub=refresh_token_payload.sub
    )
    raise litestar_raise(
        error_model=error.UpdateTokens,
        headers={
            "Set-Cookie":
                f"refresh_token={new_refresh_token.encode()}; HttpOnly; Path=/; Secure",
            "Authorization": f"Bearer {new_access_token.encode}"
        }
    )
