# flake8-in-file-ignores: noqa: B904, WPS110, WPS400

import ast

from litestar.handlers import get
from litestar.openapi.spec import Example

from app import errors as error
from app import openapi_tags as tags
from app.config import Cache, CacheKeys, CoreConfig, DataBase
from app.db.exc import TeamsNotExistsError
from app.errors import litestar_raise, litestar_response_spec
from app.handlers.controller import BaseController
from app.handlers.dto import (FullTeamDTO, QueueDTO, QueueListDTO, RaiderDTO,
                              TeamDTO, UserDTO)


class CoreController(BaseController[CoreConfig]):
    config = CoreConfig()
    path = '/'

    @get('/{team_name:str}', responses={
        422: litestar_response_spec(examples=[
            Example('TeamNotExists', value=error.TeamNotExists())
        ])
    }, tags=[tags.core_handler])
    async def get_team(
        self, db: DataBase, cache: Cache, cache_keys: CacheKeys, team_name: str
    ) -> FullTeamDTO:
        try:
            team_id = await cache.get(
                cache_keys.team_name.format(team_name)
            )
            if not team_id:
                team_id = await db.get_team_id_by_name(team_name)
                await cache.set(
                    cache_keys.team_name.format(team_name), team_id
                )

            full_team_cache = await cache.get(
                cache_keys.full_team.format(team_id)
            )
            if not full_team_cache:
                team, queues = await db.get_full_team(team_id)
                full_team = FullTeamDTO(
                    team=TeamDTO(
                        id=team.id,
                        name=team.name,
                        addon=team.addon,
                        is_vip=team.is_vip,
                        vip_end=team.vip_end,
                        owner_id=team.owner_id
                    ),
                    owner=UserDTO(
                        id=team.owner.id,
                        username=team.owner.username,
                        email=team.owner.email,
                        is_active=team.owner.is_active
                    ),
                    queues=[
                        QueueListDTO(
                            team_id=team.id,
                            wow_item_id=queue[0].wow_item_id,
                            queue=[
                                QueueDTO(
                                    position=index.position,
                                    raider=RaiderDTO(
                                        id=index.raider.id,
                                        name=index.raider.name,
                                        team_id=index.raider.team_id,
                                        class_name=index.raider.class_name,
                                        is_active=index.raider.is_active
                                    ),
                                ) for index in queue
                            ]
                        ) for queue in queues
                    ]
                )
                await cache.set(
                    cache_keys.full_team.format(team_id), str(full_team.model_dump())
                )
            else:
                full_team = FullTeamDTO(**ast.literal_eval(full_team_cache))

            return full_team

        except TeamsNotExistsError:
            raise litestar_raise(error.TeamNotExists)
