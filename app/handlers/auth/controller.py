# flake8-in-file-ignores: noqa: B904, WPS11

from litestar import status_codes as status
from litestar.controller import Controller
from litestar.exceptions import HTTPException
from litestar.handlers import get, post
from litestar.response import Template

from app import error_codes as error_code
from app.config import (EMAIL_REGISTRATION_BODY, EMAIL_REGISTRATION_SUBJECT,
                        AuthConfig, DataBase, Language, Mailer, TaskManager,
                        Token, TokenConfigType)
from app.db.exc import (ActivateUserError, InvalidCredentialsError,
                        UniqueEmailError, UniqueUsernameError)
from app.handlers.auth.dto import (RequestAuthDTO, RequestRegistrationDTO,
                                   ResponseAccessRefreshTokensDTO)
from app.handlers.auth.service import AuthService
from app.mailers.base import NonExistentEmail
from app.tokens.base import DecodeTokenError
from app.tokens.payloads import RegistrationTokenPayload


class AuthController(Controller):
    service = AuthService()
    config = AuthConfig()

    @get('/registration')
    async def registration_get(self) -> Template:
        return Template(template_name='registration.html')

    @post('/registration')
    async def registration_post(
        self, db: DataBase, mailer: Mailer, lang: Language, token_type: type[Token],
        token_config: TokenConfigType, task_manager: TaskManager,
        data: RequestRegistrationDTO
    ) -> None:
        try:
            await self.service.check_user_uniqueness(
                db=db,
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

        registration_token = self.service.create_registration_token(
            sub=data.username,
            token_type=token_type,
            token_config=token_config,
            token_exp=self.config.registration_token_exp
        )

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

        await self.service.registration(
            db=db,
            username=data.username,
            email=data.email,
            password=data.password,
            task_manager=task_manager,
            del_inactive_user_after=AuthConfig.del_inactive_user_after
        )

    @get('/verify-email/{registration_token:str}')
    async def verify_email(
        self, db: DataBase, token_type: type[Token], token_config: TokenConfigType,
        registration_token: str
    ) -> ResponseAccessRefreshTokensDTO:
        try:
            encode_registration_token = (
                await self.service.verify_registration_token(
                    token=registration_token,
                    token_type=token_type,
                    token_config=token_config
                )
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
            user_id = await self.service.activate_user(
                db=db,
                username=username
            )
        except ActivateUserError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.user_is_active
            )

        access_token = await self.service.create_access_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        refresh_token = await self.service.create_refresh_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        return ResponseAccessRefreshTokensDTO(
            access_token=access_token.encode(),
            refresh_token=refresh_token.encode()
        )

    @post('/auth')
    async def auth(
        self, db: DataBase, token_type: type[Token], token_config: TokenConfigType,
        data: RequestAuthDTO
    ) -> ResponseAccessRefreshTokensDTO:
        try:
            user_id = await self.service.verify_username_password(
                db=db,
                username=data.username,
                password=data.password
            )
        except InvalidCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.invalid_credentials
            )

        access_token = await self.service.create_access_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        refresh_token = await self.service.create_refresh_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.access_token_exp,
            sub=user_id
        )

        return ResponseAccessRefreshTokensDTO(
            access_token=access_token.encode(),
            refresh_token=refresh_token.encode()
        )
