from datetime import datetime

from app.db.abc.base import BaseAsyncDB
from app.db.abc.models import TeamProtocol
from app.db.enums import EnumAddons
from app.db.exc import DatabaseError, TeamsNotExistsError
from app.db.sqlalchemy.models import get_id
from app.types import Sentinel


class TeamsService:

    @staticmethod
    async def get_team_by_name_or_id(db: BaseAsyncDB, name: str | None = Sentinel,
                                     id: str | None = Sentinel) -> TeamProtocol:
        try:
            team = await db.get_team(name=name, id=id)
            return team
        except TeamsNotExistsError as e:
            raise e

    @staticmethod
    async def create_team(db: BaseAsyncDB, name: str, addon: EnumAddons, owner_id: str,
                          password: str, id: str = Sentinel) -> TeamProtocol:
        try:
            team = await db.create_team(
                id=get_id() if id is Sentinel else id,
                name=name,
                addon=addon,
                vip_end=None,
                owner_id=owner_id,
                password=password,

            )
            return team
        except Exception as e:
            raise e

    @staticmethod
    async def delete_team(db: BaseAsyncDB, team_id: str) -> None:
        try:
            await db.del_team(team_id)
        except Exception as e:
            raise e

    @staticmethod
    async def update_team(db: BaseAsyncDB, id: str, name: str = Sentinel,
                          addon: EnumAddons = Sentinel, is_vip: bool = Sentinel,
                          vip_end: datetime = Sentinel, password: str = Sentinel,
                          ) -> TeamProtocol:
        try:
            return await db.update_team(
                id=id,
                name=name,
                addon=addon,
                is_vip=is_vip,
                vip_end=vip_end,
                password=password
            )

        except TeamsNotExistsError as e:
            raise e

        except Exception as e:
            raise DatabaseError from e
