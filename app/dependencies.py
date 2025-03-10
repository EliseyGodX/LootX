# flake8-in-file-ignores: noqa: B904

from datetime import datetime

from litestar import status_codes as status
from litestar.connection import Request
from litestar.exceptions import HTTPException

from app import error_codes as error_code
from app.config import AuthConfig, Language
from app.tokens.base import (BaseToken, BaseTokenConfig, DecodeTokenError,
                             TokenExpiredError)
from app.tokens.payloads import AccessTokenPayload, RefreshTokenPayload


def get_language(request: Request) -> Language:
    lang = request.cookies.get('language', Language.en.value)
    try:
        lang = Language(lang)
    except ValueError:
        raise HTTPException(  # noqa: B904
            status_code=status.HTTP_400_BAD_REQUEST,
            extra=error_code.invalid_lang_cookie
        )
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            extra=error_code.access_token_invalid
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            extra=error_code.authorization_header_missing
        )

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            extra=error_code.refresh_token_invalid
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            extra=error_code.refresh_token_cookie_missing
        )

    new_access_token = token_type(
        payload=AccessTokenPayload(
            exp=(datetime.now() + AuthConfig.access_token_exp).timestamp(),
            sub=refresh_token_payload.sub,
        ),
        config=token_config
    )

    new_refresh_token = token_type(
        payload=RefreshTokenPayload(
            exp=(datetime.now() + AuthConfig.refresh_token_exp).timestamp(),
            sub=refresh_token_payload.sub,
        ),
        config=token_config
    )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=new_access_token.encode(),
        extra=error_code.update_tokens,
        headers={
            "Set-Cookie":
                f"refresh_token={new_refresh_token.encode()}; HttpOnly; Path=/; Secure"
        }
    )
