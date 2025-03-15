
from pydantic import Field

from app.config import RaiderConfig
from app.db.enums import EnumClasses
from app.handlers.abc.dto import BaseDTO
from app.types import TeamId


class ResponseRaiderDTO(BaseDTO):
    id: str
    name: str
    team_id: TeamId
    class_name: EnumClasses
    is_active: bool


class RequestCreateRaiderDTO(BaseDTO):
    name: str = Field(..., min_length=RaiderConfig.name_min_length,
                      max_length=RaiderConfig.name_max_length)
    team_id: TeamId
    class_name: EnumClasses
    is_active: bool = True
