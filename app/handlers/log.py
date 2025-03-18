import ast

from litestar.handlers import get

from app import openapi_tags as tags
from app.config import DataBase, LogConfig
from app.handlers.controller import BaseController
from app.handlers.dto import LogDTO, LogListDTO
from app.types import TeamId


class LogController(BaseController[LogConfig]):
    config = LogConfig()
    path = '/log'

    @get('/logs', tags=[tags.log_handler])
    async def get_logs(
        self, db: DataBase, team_id: TeamId, limit: int | None = None,
        offset: int | None = None, wow_item_id: int | None = None
    ) -> LogListDTO:
        return LogListDTO(
            team_id=team_id,
            wow_item_id=wow_item_id,
            limit=limit,
            offset=offset,
            logs=[
                LogDTO(
                    created_at=log.created_at,
                    queue=ast.literal_eval(log.queue)
                ) for log in await db.get_logs(
                    team_id=team_id,
                    limit=limit,
                    offset=offset,
                    wow_item_id=wow_item_id
                )
            ]
        )
