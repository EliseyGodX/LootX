# flake8-in-file-ignores: noqa: B904, WPS110, WPS400

from litestar.handlers import delete, get, post
from litestar.openapi.spec import Example

from app import errors as error
from app import openapi_tags as tags
from app.config import DataBase, Language, QueueConfig, WoWAPI, Cache, CacheKeys
from app.db.exc import (RaiderNotFoundError, TeamsNotExistsError,
                        WoWItemNotFoundError)
from app.errors import litestar_raise, litestar_response_spec
from app.handlers.controller import BaseController
from app.handlers.dto import CreateQueueDTO, QueueDTO, QueueListDTO, RaiderDTO
from app.tokens.payloads import AccessTokenPayload
from app.types import TeamId


class QueueController(BaseController[QueueConfig]):
    config = QueueConfig()
    path = '/queue'

    @get('/', tags=[tags.queue_handler])
    async def get_queue(
        self, db: DataBase, team_id: TeamId, wow_item_id: int
    ) -> QueueListDTO:
        return QueueListDTO(
            team_id=team_id,
            wow_item_id=wow_item_id,
            queue=[
                QueueDTO(
                    position=queue.position,
                    raider=RaiderDTO(
                        id=queue.raider.id,
                        name=queue.raider.name,
                        team_id=queue.raider.team_id,
                        class_name=queue.raider.class_name,
                        is_active=queue.raider.is_active
                    ),
                ) for queue
                in await db.get_queue_by_item(team_id, wow_item_id)
            ]
        )

    @post('/', responses={
        401: litestar_response_spec(examples=[
            Example('AccessTokenInvalid', value=error.AccessTokenInvalid()),
            Example('AccessTokenExpired', value=error.AccessTokenExpired()),
            Example('AuthorizationHeaderMissing', value=error.AuthorizationHeaderMissing())  # noqa
        ]),
        403: litestar_response_spec(examples=[
            Example('UserNotTeamOwner', value=error.UserNotTeamOwner())
        ]),
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists()),
            Example('RaiderNotExists', value=error.RaiderNotExists()),
            Example('ItemNotExists', value=error.ItemNotExists())
        ])
    }, tags=[tags.queue_handler])
    async def update_queue(
        self, auth_client: AccessTokenPayload, db: DataBase, cache: Cache,
        cache_keys: CacheKeys, lang: Language, wow_api: WoWAPI, data: CreateQueueDTO
    ) -> QueueListDTO:
        try:
            team = await db.get_team_with_owner(data.team_id)
        except TeamsNotExistsError:
            raise litestar_raise(error.TeamNotExists)

        if team.owner.id != auth_client.sub:
            raise litestar_raise(error.UserNotTeamOwner)

        try:
            queue_list = QueueListDTO(
                team_id=data.team_id,
                wow_item_id=data.wow_item_id,
                queue=[
                    QueueDTO(
                        position=queue.position,
                        raider=RaiderDTO(
                            id=queue.raider.id,
                            name=queue.raider.name,
                            team_id=queue.raider.team_id,
                            class_name=queue.raider.class_name,
                            is_active=queue.raider.is_active
                        ),
                    ) for queue
                    in await db.create_queue(
                        team_id=data.team_id,
                        wow_item_id=data.wow_item_id,
                        addon=team.addon,
                        lang=self.lang_to_enumlang(lang),
                        raiders=data.raiders,
                        wow_api=wow_api
                    )
                ]
            )
            await db.create_log(
                team_id=data.team_id,
                user_id=auth_client.sub,
                wow_item_id=data.wow_item_id,
                queue=str([queue.model_dump() for queue in queue_list.queue])
            )
            await cache.del_key(
                cache_keys.full_team.format(team.id)
            )
            return queue_list
        except RaiderNotFoundError:
            raise litestar_raise(error.RaiderNotExists)
        except WoWItemNotFoundError:
            raise litestar_raise(error.ItemNotExists)

    @delete('/', responses={
        401: litestar_response_spec(examples=[
            Example('AccessTokenInvalid', value=error.AccessTokenInvalid()),
            Example('AccessTokenExpired', value=error.AccessTokenExpired()),
            Example('AuthorizationHeaderMissing', value=error.AuthorizationHeaderMissing())  # noqa
        ]),
        403: litestar_response_spec(examples=[
            Example('UserNotTeamOwner', value=error.UserNotTeamOwner())
        ]),
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists()),
            Example('QueueNotExists', value=error.QueueNotExists())
        ])
    }, tags=[tags.queue_handler])
    async def delete_queue(
        self, auth_client: AccessTokenPayload, db: DataBase, cache: Cache,
        cache_keys: CacheKeys, team_id: TeamId, wow_item_id: int
    ) -> None:
        try:
            owner = await db.get_team_owner(team_id)
        except TeamsNotExistsError:
            raise litestar_raise(error.TeamNotExists)

        if owner.id != auth_client.sub:
            raise litestar_raise(error.UserNotTeamOwner)

        if not await db.is_queue_exists(team_id, wow_item_id):
            raise litestar_raise(error.QueueNotExists)

        await cache.del_key(
            cache_keys.full_team.format(team_id)
        )

        await db.del_queue(team_id, wow_item_id)
