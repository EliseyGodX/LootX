import logging

from pydantic import BaseModel


class BaseMailerConfig(BaseModel):
    self_email: str
    logger: logging.Logger

    class Config:
        arbitrary_types_allowed = True


class SMTPConfig(BaseMailerConfig):
    smtp_server: str
    smtp_user: str
    smtp_password: str
    smtp_port: int = 587
