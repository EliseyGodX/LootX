from json import JSONEncoder
from typing import Optional

from pydantic import BaseModel


class BaseTokenConfig(BaseModel):

    class Config:
        arbitrary_types_allowed = True


class JWTokenConfig(BaseTokenConfig):
    alg: str
    typ: str
    key: str
    json_encoder: Optional[type[JSONEncoder]] = None
    sort_headers: bool = True
