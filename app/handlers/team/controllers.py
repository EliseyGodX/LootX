# flake8-in-file-ignores: noqa: B904, WPS110

from litestar import status_codes as status
from litestar.controller import Controller
from litestar.exceptions import HTTPException
from litestar.handlers import delete, get, patch, post
from litestar.response import Redirect, Template

from app import error_codes as error_code
from app.config import DataBase, TeamConfig
from app.db.exc import (TeamsAlreadyExistsError, TeamsNotExistsError,
                        UserNotExistsError)
from app.handlers.team.dto import (RequestCreateTeamDTO, RequestUpdateTeamDTO,
                                   ResponseTeamDTO)
from app.handlers.team.services import TeamService
from app.types import Sentinel


class TeamController(Controller):
    service = TeamService()
    config = TeamConfig()

    @get('/team/{name:str}')
    async def team_get_by_name(self, db: DataBase, name: str) -> Template:
        try:
            team = await self.service.get_team_by_name(db=db, name=name)
            return Template(template_name='team.html', context={"team": team})
        except TeamsNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.team_not_exists
            )

    @get('/team')
    async def team_get(self) -> Template:
        return Template(template_name='teams.html')

    @post('/team')
    async def create_team(self, db: DataBase, data: RequestCreateTeamDTO) -> Redirect:
        try:
            await self.service.create_team(
                db=db,
                name=data.name,
                addon=data.addon,
                password=data.password,
                owner_id='01JP02S1TDQ2R48TE3D6QZJCH7'
            )

            return Redirect('/')

        except TeamsAlreadyExistsError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                extra=error_code.team_name_not_unique
            )
        except UserNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.user_not_exists
            )

    @delete('/team/{team_id:str}')
    async def delete_team(self, db: DataBase, team_id: str) -> None:
        try:
            await self.service.delete_team(
                db=db,
                team_id=team_id
            )
        except TeamsNotExistsError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                extra=error_code.team_not_exists
            )

    @patch('/team/{team_id:str}')
    async def update_team(
        self, db: DataBase, team_id: str, data: RequestUpdateTeamDTO
    ) -> ResponseTeamDTO:
        try:
            team = await self.service.update_team(
                db=db,
                id=team_id,
                name=data.name if data.name else Sentinel,
                addon=data.addon if data.addon else Sentinel,
                is_vip=data.is_vip if data.is_vip else Sentinel,
                vip_end=data.vip_end if data.vip_end else Sentinel,
                password=data.password if data.password else Sentinel
            )
            return ResponseTeamDTO(
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
