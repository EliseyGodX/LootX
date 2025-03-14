# flake8-in-file-ignores: noqa: B904, WPS110, WPS400

from litestar.handlers import delete, get, patch, post
from litestar.openapi.spec import Example

from app import errors as error
from app import openapi_tags as tags
from app.config import (EMAIL_DELETE_TEAM_BODY, EMAIL_DELETE_TEAM_SUBJECT,
                        DataBase, Language, Mailer, TeamConfig, Token,
                        TokenConfigType)
from app.db.exc import TeamsAlreadyExistsError, TeamsNotExistsError
from app.dependencies import DecodeTokenError
from app.errors import litestar_raise, litestar_response_spec
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

    @get('/{name:str}', responses={
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    })
    async def get_team_by_name(self, db: DataBase, name: str) -> ResponseTeamDTO:
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
            raise litestar_raise(error.TeamNotExists)

    @post('/', responses={
        401: litestar_response_spec(examples=[
            Example('AccessTokenInvalid', value=error.AccessTokenInvalid()),
            Example('AuthorizationHeaderMissing', value=error.AuthorizationHeaderMissing()),  # noqa
            Example('RefreshTokenInvalid', value=error.RefreshTokenInvalid()),
            Example('RefreshTokenCookieMissing', value=error.RefreshTokenCookieMissing()),  # noqa
            Example('UpdateTokens', value=error.UpdateTokens())
        ]),
        409: litestar_response_spec(examples=[
            Example('TeamNameNotUnique', value=error.TeamNameNotUnique())
        ])
    }, tags=[tags.requires_authorization])
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
            raise litestar_raise(error.TeamNameNotUnique)

    @post('delete-request/{team_name:str}', responses={
        401: litestar_response_spec(examples=[
            Example('AccessTokenInvalid', value=error.AccessTokenInvalid()),
            Example('AuthorizationHeaderMissing', value=error.AuthorizationHeaderMissing()),  # noqa
            Example('RefreshTokenInvalid', value=error.RefreshTokenInvalid()),
            Example('RefreshTokenCookieMissing', value=error.RefreshTokenCookieMissing()),  # noqa
            Example('UpdateTokens', value=error.UpdateTokens())
        ]),
        403: litestar_response_spec(examples=[
            Example('UserNotTeamOwner', value=error.UserNotTeamOwner())
        ]),
        422: litestar_response_spec(examples=[
            Example('EmailNonExistent', value=error.EmailNonExistent()),
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    }, tags=[tags.requires_authorization])
    async def delete_request_team(
        self, auth_client: AccessTokenPayload, db: DataBase, mailer: Mailer,
        token_type: type[Token], token_config: TokenConfigType, lang: Language,
        team_name: str
    ) -> None:
        try:
            team = await db.get_team_by_name_with_owner(team_name)
        except TeamsNotExistsError:
            raise litestar_raise(error.TeamNotExists)

        if team.owner.id != auth_client.sub:
            raise litestar_raise(error.UserNotTeamOwner)

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
            raise litestar_raise(error.EmailNonExistent)

    @delete('delete/{delete_team_token:str}', responses={
        401: litestar_response_spec(examples=[
            Example('AccessTokenInvalid', value=error.AccessTokenInvalid()),
            Example('AuthorizationHeaderMissing', value=error.AuthorizationHeaderMissing()),  # noqa
            Example('RefreshTokenInvalid', value=error.RefreshTokenInvalid()),
            Example('RefreshTokenCookieMissing', value=error.RefreshTokenCookieMissing()),  # noqa
            Example('UpdateTokens', value=error.UpdateTokens())
        ]),
        422: litestar_response_spec(examples=[
            Example('DeleteTeamTokenInvalid', value=error.DeleteTeamTokenInvalid()),  # noqa: E501
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    }, tags=[tags.requires_authorization])
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
            raise litestar_raise(error.DeleteTeamTokenInvalid)

        try:
            team = await db.get_team_with_owner(delete_team_token_payload.sub)
        except TeamsNotExistsError:
            raise litestar_raise(error.TeamNotExists)

        if team.owner.id != auth_client.sub:
            raise litestar_raise(error.UserNotTeamOwner)

        await db.del_team(delete_team_token_payload.sub)

    @patch('/{team_id:str}', responses={
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    })
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
            raise litestar_raise(error.TeamNotExists)
