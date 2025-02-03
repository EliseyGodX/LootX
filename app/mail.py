import abc
import logging
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Self

import aiosmtplib

from app.config import SELF_EMAIL, SERVICE_NAME
from app.types import Sentinel


@dataclass(kw_only=True)
class BaseAsyncEmail(abc.ABC):
    logger: logging.Logger
    self_email: str = SELF_EMAIL

    @abc.abstractmethod
    async def connect(self) -> Self: ...

    @abc.abstractmethod
    async def send(self, subject: str, body: str,
                   to_email: str) -> None: ...

    @abc.abstractmethod
    async def close(self) -> None: ...


@dataclass(kw_only=True)
class AsyncSMTPEmail(BaseAsyncEmail):
    smtp_server: str
    smtp_user: str
    smtp_password: str
    smtp_port: int = 587
    smtp_session: aiosmtplib.SMTP = Sentinel

    async def connect(self) -> Self:
        try:
            if not self.smtp_session:
                self.smtp_session = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    use_tls=True,
                )
                await self.smtp_session.connect()
            await self.smtp_session.noop()
        except Exception as e:
            self.logger.warning(e)

        return self

    async def send(self, subject: str, body: str, to_email: str) -> None:
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((SERVICE_NAME, self.smtp_user))
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            await self.smtp_session.send_message(msg)

        except Exception as e:
            self.logger.warning(e)

    async def close(self) -> None:
        if self.smtp_session:
            self.smtp_session.close()
            self.smtp_session = Sentinel
