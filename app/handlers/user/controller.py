# flake8-in-file-ignores: noqa: B904, WPS110
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.handlers import get, patch, post

from app import error_codes as error_code
from app.config import (EMAIL_CHANGE_PASSWORD_BODY,
                        EMAIL_CHANGE_PASSWORD_SUBJECT, DataBase, Language,
                        Mailer, Token, TokenConfigType, UserConfig)
from app.db.exc import UserNotFoundError
from app.handlers.abc.controller import BaseController
from app.handlers.user.dto import RequestChangePasswordDTO, ResponseUserDTO
from app.mailers.base import NonExistentEmail
from app.tokens.base import (ChangePasswordTokenPayload, DecodeTokenError,
                             create_change_password_token,
                             verify_change_password_token)
from app.tokens.payloads import AccessTokenPayload
from app.types import UserId, Username


class UserController(BaseController[UserConfig]):
    config = UserConfig()
    path = '/user'

    @get('/username/{username:str}')
    async def get_user_by_username(
        self, db: DataBase, username: Username
    ) -> ResponseUserDTO:
        try:
            user = await db.get_user_by_username(username)
            return ResponseUserDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                password=user.password
            )
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                extra=error_code.user_not_exists
            )

    @get('/id/{user_id:str}')
    async def get_user_by_id(
        self, db: DataBase, user_id: UserId
    ) -> ResponseUserDTO:
        try:
            user = await db.get_user(user_id)
            return ResponseUserDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                password=user.password
            )
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                extra=error_code.user_not_exists
            )

    @post('/change-password-request')
    async def change_password_request(
        self, auth_client: AccessTokenPayload, db: DataBase, mailer: Mailer,
        lang: Language, token_type: type[Token], token_config: TokenConfigType
    ) -> None:
        try:
            user_email = await db.get_user_email(auth_client.sub)
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                extra=error_code.user_not_exists
            )

        change_password_token = create_change_password_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.change_password_token_exp,
            sub=auth_client.sub
        )

        try:
            await mailer.send(
                subject=EMAIL_CHANGE_PASSWORD_SUBJECT[lang],
                body=EMAIL_CHANGE_PASSWORD_BODY[lang].format(
                    change_password_token.encode()
                ),
                to_email=user_email
            )
        except NonExistentEmail:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                extra=error_code.email_non_existent
            )

    @patch('change-password/{change_password_token:str}')
    async def change_password(
        self, auth_client: AccessTokenPayload, db: DataBase, token_type: type[Token],
        token_config: TokenConfigType, data: RequestChangePasswordDTO,
        change_password_token: str
    ) -> None:
        try:
            encode_change_password_token = verify_change_password_token(
                token=change_password_token,
                token_type=token_type,
                token_config=token_config
            )
            change_password_token_payload: ChangePasswordTokenPayload = (
                encode_change_password_token.payload
            )  # type: ignore
        except DecodeTokenError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.delete_team_token_invalid
            )

        if auth_client.sub != change_password_token_payload.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.tokens_subject_not_equal
            )

        await db.change_user_password(
            id=auth_client.sub,
            new_password=data.password
        )
