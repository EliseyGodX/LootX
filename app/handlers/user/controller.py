# flake8-in-file-ignores: noqa: B904, WPS110

from litestar.controller import Controller
from litestar.handlers import get
from litestar.response import Template

from app.config import DataBase, UserConfig
from app.handlers.user.service import UserService
from app.tokens.payloads import AccessTokenPayload


class UserController(Controller):
    service = UserService
    config = UserConfig

    @get('/account')
    async def account_get(self, auth_client: AccessTokenPayload, db: DataBase
                          ) -> Template:
        user = await self.service.get_user(
            db=db,
            user_id=auth_client.sub
        )
        return Template(template_name='...')
