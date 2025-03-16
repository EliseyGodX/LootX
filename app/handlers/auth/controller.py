# flake8-in-file-ignores: noqa: B904, WPS11, WPS400

from litestar.handlers import get, post
from litestar.openapi.spec import Example
from litestar.response import Response

from app import errors as error
from app import openapi_tags as tags
from app.config import (EMAIL_REGISTRATION_BODY, EMAIL_REGISTRATION_SUBJECT,
                        AuthConfig, DataBase, Language, Mailer, TaskManager,
                        Token, TokenConfigType)
from app.db.exc import (ActivateUserError, InvalidCredentialsError,
                        UniqueEmailError, UniqueUsernameError)
from app.errors import litestar_raise, litestar_response_spec
from app.handlers.abc.controller import BaseController
from app.handlers.auth.dto import RequestAuthDTO, RequestRegistrationDTO
from app.mailers.base import NonExistentEmail
from app.task_managers.base import TaskManagerError
from app.tokens.base import (DecodeTokenError, create_access_token,
                             create_refresh_token, create_registration_token,
                             verify_registration_token)
from app.tokens.payloads import RegistrationTokenPayload


class AuthController(BaseController[AuthConfig]):
    config = AuthConfig()
    path = '/auth'

    @post('/registration', responses={
        409: litestar_response_spec(examples=[
            Example('UsernameNotUnique', value=error.UsernameNotUnique()),
            Example('EmailNotUnique', value=error.EmailNotUnique())
        ]),
        422: litestar_response_spec(examples=[
            Example('EmailNonExistent', value=error.EmailNonExistent())
        ])
    }, tags=[tags.auth_handler])
    async def registration(
        self, db: DataBase, mailer: Mailer, lang: Language, token_type: type[Token],
        token_config: TokenConfigType, task_manager: TaskManager,
        data: RequestRegistrationDTO
    ) -> None:
        try:
            await db.is_user_username_email_unique(
                username=data.username,
                email=data.email
            )
        except UniqueUsernameError:
            raise litestar_raise(error.UsernameNotUnique)
        except UniqueEmailError:
            raise litestar_raise(error.EmailNotUnique)

        registration_token = create_registration_token(
            token_type=token_type,
            token_config=token_config,
            token_exp=self.config.registration_token_exp,
            sub=data.username
        ).encode()

        try:
            await mailer.send(
                subject=EMAIL_REGISTRATION_SUBJECT[lang],
                body=EMAIL_REGISTRATION_BODY[lang].format(registration_token),
                to_email=data.email
            )
        except NonExistentEmail:
            raise litestar_raise(error.EmailNonExistent)

        registration_user = await db.create_user(
            username=data.username,
            password=data.password,
            email=data.email,
            is_active=False
        )
        try:
            await task_manager.del_inactive_user(
                user_id=registration_user.id,
                eta_delta=self.config.del_inactive_user_after
            )
        except Exception as e:
            await db.del_user(registration_user.id)
            raise TaskManagerError from e

    @get('/verify-email/{registration_token:str}', responses={
        403: litestar_response_spec(examples=[
            Example('UserIsActive', value=error.UserIsActive())
        ]),
        422: litestar_response_spec(examples=[
            Example('RegistrationTokenInvalid', value=error.RegistrationTokenInvalid())  # noqa
        ])
    }, tags=[tags.auth_handler])
    async def verify_email(
        self, db: DataBase, token_type: type[Token], token_config: TokenConfigType,
        registration_token: str
    ) -> Response[None]:
        try:
            encode_registration_token = verify_registration_token(
                token=registration_token,
                token_type=token_type,
                token_config=token_config
            )
            registration_token_payload: RegistrationTokenPayload = (
                encode_registration_token.payload
            )  # type: ignore
            username = registration_token_payload.sub
        except DecodeTokenError:
            raise litestar_raise(error.RegistrationTokenInvalid)

        try:
            user_id = await db.activate_user(username)
        except ActivateUserError:
            raise litestar_raise(error.UserIsActive)

        access_token = create_access_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        refresh_token = create_refresh_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        return Response(
            content=None,
            headers={
                "Set-Cookie":
                    f"refresh_token={refresh_token.encode()}; HttpOnly; Path=/; Secure",
                "Authorization": f"Bearer {access_token.encode}"
            }
        )

    @post('/', responses={
        401: litestar_response_spec(examples=[
            Example('InvalidCredentials', value=error.InvalidCredentials())
        ])
    }, tags=[tags.auth_handler])
    async def authentication(
        self, db: DataBase, token_type: type[Token], token_config: TokenConfigType,
        data: RequestAuthDTO
    ) -> Response[None]:
        try:
            user_id = await db.verify_username_password(
                username=data.username,
                password=data.password
            )
        except InvalidCredentialsError:
            raise litestar_raise(error.InvalidCredentials)

        access_token = create_access_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        refresh_token = create_refresh_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        return Response(
            content=None,
            headers={
                "Set-Cookie":
                    f"refresh_token={refresh_token.encode()}; HttpOnly; Path=/; Secure",
                "Authorization": f"Bearer {access_token.encode}"
            }
        )
