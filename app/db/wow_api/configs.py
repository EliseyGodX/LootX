import logging

import httpx
from pydantic import BaseModel


class BaseWoWAPIConfig(BaseModel):
    logger: logging.Logger
    url: str
    icon_url: str

    class Config:
        arbitrary_types_allowed = True


class WoWHeadAPIConfig(BaseWoWAPIConfig):
    httpx_client: httpx.AsyncClient = httpx.AsyncClient()
