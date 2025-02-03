from enum import Enum
from typing import Generic, TypeAlias, TypeVar

from pydantic import BaseModel

Type = TypeVar("Type", bound="TokenType")

UserId: TypeAlias = str


class TokenType(str, Enum):
    access = "ACCESS"
    refresh = "REFRESH"
    registration = "REGISTRATION"


class TokenPayload(BaseModel, Generic[Type]):
    type: Type
    sub: UserId
    exp: int

    class Config:
        use_enum_values = True
