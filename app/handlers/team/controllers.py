# flake8-in-file-ignores: noqa: B904, WPS110

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.handlers import delete, get, patch, post

from app import error_codes as error_code
from app.config import (EMAIL_DELETE_TEAM_BODY, EMAIL_DELETE_TEAM_SUBJECT,
                        DataBase, Language, Mailer, TeamConfig, Token,
                        TokenConfigType)
from app.db.exc import TeamsAlreadyExistsError, TeamsNotExistsError
from app.dependencies import DecodeTokenError
from app.handlers.abc.controller import BaseController
from app.handlers.team.dto import (RequestCreateTeamDTO, RequestUpdateTeamDTO,
                                   ResponseTeamDTO)
from app.mailers.base import NonExistentEmail
from app.tokens.base import (DeleteTeamTokenPayload, create_delete_team_token,
                             verify_delete_team_token)
from app.tokens.payloads import AccessTokenPayload
from app.types import DeleteTeamToken


class TeamController(BaseController[TeamConfig]):
    config = TeamConfig()
    path = '/team'

    @get('/{name:str}')
    async def team_get_by_name(self, db: DataBase, name: str) -> ResponseTeamDTO:
        try:
            team = await db.get_team_by_name(name)
            return ResponseTeamDTO(
                id=team.id,
                name=team.name,
                addon=team.addon,
                is_vip=team.is_vip,
                vip_end=team.vip_end,
                owner_id=team.owner_id,
                password=team.password
            )
        except TeamsNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.team_not_exists
            )

    @post('/')
    async def create_team(
        self, auth_client: AccessTokenPayload, db: DataBase, data: RequestCreateTeamDTO
    ) -> ResponseTeamDTO:
        try:
            team = await db.create_team(
                name=data.name,
                addon=data.addon,
                owner_id=auth_client.sub,
                password=data.password,
            )
            return ResponseTeamDTO(
                id=team.id,
                name=team.name,
                addon=team.addon,
                is_vip=team.is_vip,
                vip_end=team.vip_end,
                owner_id=team.owner_id,
                password=team.password
            )

        except TeamsAlreadyExistsError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                extra=error_code.team_name_not_unique
            )

    @post('delete-request/{team_name:str}')
    async def delete_request_team(
        self, auth_client: AccessTokenPayload, db: DataBase, mailer: Mailer,
        token_type: type[Token], token_config: TokenConfigType, lang: Language,
        team_name: str
    ) -> None:
        try:
            team = await db.get_team_by_name_with_owner(team_name)
        except TeamsNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.team_not_exists
            )

        if team.owner.id != auth_client.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.user_not_team_owner
            )

        delete_team_token = create_delete_team_token(
            token_type=token_type,
            token_config=token_config,
            exp=self.config.delete_team_token_exp,
            sub=team.id
        )

        try:
            await mailer.send(
                subject=EMAIL_DELETE_TEAM_SUBJECT[lang],
                body=EMAIL_DELETE_TEAM_BODY[lang].format(
                    delete_team_token.encode()
                ),
                to_email=team.owner.email
            )
        except NonExistentEmail:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                extra=error_code.email_non_existent
            )

    @delete('delete/{delete_team_token:str}')
    async def delete_team(
        self, auth_client: AccessTokenPayload, db: DataBase, token_type: type[Token],
        token_config: TokenConfigType, delete_team_token: DeleteTeamToken
    ) -> None:
        try:
            encode_delete_team_token = verify_delete_team_token(
                token=delete_team_token,
                token_type=token_type,
                token_config=token_config
            )
            delete_team_token_payload: DeleteTeamTokenPayload = (
                encode_delete_team_token.payload
            )  # type: ignore
        except DecodeTokenError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.delete_team_token_invalid
            )

        try:
            team = await db.get_team_with_owner(delete_team_token_payload.sub)
        except TeamsNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.team_not_exists
            )

        if team.owner.id != auth_client.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                extra=error_code.user_not_team_owner
            )

        await db.del_team(delete_team_token_payload.sub)

    @patch('/{team_id:str}')
    async def update_team(
        self, db: DataBase, team_id: str, data: RequestUpdateTeamDTO
    ) -> ResponseTeamDTO:
        try:
            team = await db.update_team(
                id=team_id,
                name=data.name,
                addon=data.addon,
                password=data.password
            )
            return ResponseTeamDTO(
                id=team.id,
                name=team.name,
                addon=team.addon,
                is_vip=team.is_vip,
                vip_end=team.vip_end,
                owner_id=team.owner_id,
                password=team.password,
            )

        except TeamsNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.team_not_exists
            )
