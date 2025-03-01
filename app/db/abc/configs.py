from pydantic import BaseModel


class BaseDBConfig(BaseModel):
    db_url: str
