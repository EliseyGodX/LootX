# flake8-in-file-ignores: noqa: B904, WPS110

from litestar import status_codes as status
from litestar.controller import Controller
from litestar.exceptions import HTTPException
from litestar.handlers import get, post
from litestar.response import Template

from app.config import (EMAIL_REGISTRATION_BODY, EMAIL_REGISTRATION_SUBJECT,
                        JWT_ALGORITHM, JWT_KEY, REGISTRATION_TOKEN_EXP,
                        Language)
from app.dto import RequestRegistrationPostDTO
from app.error_codes import ErrorCodes
from app.mail import NonExistentEmail
from app.services import AuthService, UniqueEmailError, UniqueUsernameError
from app.types import Mailer


class AuthController(Controller):
    auth_service = AuthService()

    @get('/registration')
    async def registration_get(self) -> Template:
        return Template(template_name='registration.html')

    @post('/registration')
    async def registration_post(
        self, mailer: Mailer, lang: Language,
        data: RequestRegistrationPostDTO,
    ) -> None:
        try:
            await self.auth_service.check_user_uniqueness(
                username=data.username,
                email=data.email
            )
        except UniqueUsernameError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCodes.UsernameNotUnique
            )
        except UniqueEmailError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCodes.EmailNotUnique
            )

        registration_token = self.auth_service.get_registration_token(
            username=data.username,
            jwt_algorithm=JWT_ALGORITHM,
            jwt_key=JWT_KEY,
            token_exp=REGISTRATION_TOKEN_EXP
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
                detail=ErrorCodes.EmailNonExistent
            )

        await self.auth_service.registation(
            username=data.username,
            email=data.email,
            password=data.password
        )
