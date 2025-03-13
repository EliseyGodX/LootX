# flake8-in-file-ignores: noqa: B904, WPS11

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.handlers import get, post

from app import error_codes as error_code
from app.config import (EMAIL_REGISTRATION_BODY, EMAIL_REGISTRATION_SUBJECT,
                        AuthConfig, DataBase, Language, Mailer, TaskManager,
                        Token, TokenConfigType)
from app.db.exc import (ActivateUserError, InvalidCredentialsError,
                        UniqueEmailError, UniqueUsernameError)
from app.handlers.abc.controller import BaseController
from app.handlers.auth.dto import (RequestAuthDTO, RequestRegistrationDTO,
                                   ResponseAccessRefreshTokensDTO)
from app.mailers.base import NonExistentEmail
from app.task_managers.base import TaskManagerError
from app.tokens.base import (DecodeTokenError, create_access_token,
                             create_refresh_token, create_registration_token,
                             verify_registration_token)
from app.tokens.payloads import RegistrationTokenPayload


class AuthController(BaseController[AuthConfig]):
    config = AuthConfig()
    path = '/auth'

    @post('/registration')
    async def registration_post(
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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                extra=error_code.username_not_unique
            )
        except UniqueEmailError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                extra=error_code.email_not_unique
            )

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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                extra=error_code.email_non_existent
            )

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

    @get('/verify-email/{registration_token:str}')
    async def verify_email(
        self, db: DataBase, token_type: type[Token], token_config: TokenConfigType,
        registration_token: str
    ) -> ResponseAccessRefreshTokensDTO:
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.registration_token_invalid
            )

        try:
            user_id = await db.activate_user(username)
        except ActivateUserError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.user_is_active
            )

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

        return ResponseAccessRefreshTokensDTO(
            access_token=access_token.encode(),
            refresh_token=refresh_token.encode()
        )

    @post('/')
    async def auth(
        self, db: DataBase, token_type: type[Token], token_config: TokenConfigType,
        data: RequestAuthDTO
    ) -> ResponseAccessRefreshTokensDTO:
        try:
            user_id = await db.verify_username_password(
                username=data.username,
                password=data.password
            )
        except InvalidCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.invalid_credentials
            )

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

        return ResponseAccessRefreshTokensDTO(
            access_token=access_token.encode(),
            refresh_token=refresh_token.encode()
        )
