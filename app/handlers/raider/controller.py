# flake8-in-file-ignores: noqa: B904, WPS110, WPS400

from litestar.handlers import delete, get, post
from litestar.openapi.spec import Example

from app import errors as error
from app import openapi_tags as tags
from app.config import DataBase, RaiderConfig
from app.db.exc import RaiderNotFoundError, RaiderNotUnique, TeamsNotExistsError
from app.errors import litestar_raise, litestar_response_spec
from app.handlers.abc.controller import BaseController
from app.handlers.raider.dto import RequestCreateRaiderDTO, ResponseRaiderDTO
from app.tokens.payloads import AccessTokenPayload
from app.types import RaiderId


class RaiderController(BaseController[RaiderConfig]):
    config = RaiderConfig()
    path = '/raider'

    @get('/{raider_id:str}', responses={
        422: litestar_response_spec(examples=[
            Example('RaiderNotExists', value=error.RaiderNotExists())
        ])
    }, tags=[tags.raider_handler])
    async def get_raider(self, db: DataBase, raider_id: RaiderId) -> ResponseRaiderDTO:
        try:
            raider = await db.get_raider(raider_id)
            return ResponseRaiderDTO(
                id=raider.id,
                name=raider.name,
                team_id=raider.team_id,
                class_name=raider.class_name,
                is_active=raider.is_active
            )
        except RaiderNotFoundError:
            raise litestar_raise(error.RaiderNotExists)

    @post('/', responses={
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
        409: litestar_response_spec(examples=[
            Example('RaiderNotUnique', value=error.RaiderNotUnique())
        ]),
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    }, tags=[tags.requires_authorization, tags.raider_handler])
    async def create_raider(
        self, auth_client: AccessTokenPayload, db: DataBase,
        data: RequestCreateRaiderDTO
    ) -> ResponseRaiderDTO:
        try:
            owner = await db.get_team_owner(data.team_id)
        except TeamsNotExistsError:
            raise litestar_raise(error.TeamNotExists)

        if owner.id != auth_client.sub:
            raise litestar_raise(error.UserNotTeamOwner)

        try:
            raider = await db.create_raider(
                name=data.name,
                team_id=data.team_id,
                class_name=data.class_name,
                is_active=data.is_active
            )
        except RaiderNotUnique:
            raise litestar_raise(error.RaiderNotUnique)

        return ResponseRaiderDTO(
            id=raider.id,
            name=raider.name,
            team_id=raider.team_id,
            class_name=raider.class_name,
            is_active=raider.is_active
        )

    @delete('/{raider_id:str}', responses={
        401: litestar_response_spec(examples=[
            Example('AccessTokenInvalid', value=error.AccessTokenInvalid()),
            Example('AuthorizationHeaderMissing', value=error.AuthorizationHeaderMissing()),  # noqa
            Example('RefreshTokenInvalid', value=error.RefreshTokenInvalid()),
            Example('RefreshTokenCookieMissing', value=error.RefreshTokenCookieMissing()),  # noqa
            Example('UpdateTokens', value=error.UpdateTokens())
        ]),
        403: litestar_response_spec(examples=[
            Example('UserNotTeamOwner', value=error.RaiderNotExists())
        ]),
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    }, tags=[tags.requires_authorization, tags.raider_handler])
    async def delete_raider(
        self, auth_client: AccessTokenPayload, db: DataBase, raider_id: RaiderId
    ) -> None:
        try:
            raider = await db.get_raider(raider_id)
        except RaiderNotFoundError:
            raise litestar_raise(error.RaiderNotExists)

        owner = await db.get_team_owner(raider.team_id)
        if owner.id != auth_client.sub:
            raise litestar_raise(error.UserNotTeamOwner)

        await db.set_raider_inactive(raider_id)
