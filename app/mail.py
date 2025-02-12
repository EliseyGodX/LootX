import abc
import logging
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Self

import aiosmtplib


class MailerError(Exception): ...
class NonExistentEmail(MailerError): ...


@dataclass(kw_only=True)
class BaseAsyncMailer(abc.ABC):
    self_email: str
    service_name: str
    logger: logging.Logger

    @abc.abstractmethod
    async def connect(self) -> Self: ...

    @abc.abstractmethod
    async def send(self, subject: str, body: str,
                   to_email: str) -> None: ...

    @abc.abstractmethod
    async def close(self) -> None: ...


@dataclass(kw_only=True)
class AsyncSMTPMailer(BaseAsyncMailer):
    smtp_server: str
    smtp_user: str
    smtp_password: str
    smtp_port: int = 587

    async def connect(self) -> Self:
        try:
            self.smtp_session = aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=False
            )
            await self.smtp_session.connect()
            await self.smtp_session.noop()
        except Exception as e:
            self.logger.warning(e)
        return self

    async def send(self, subject: str, body: str, to_email: str) -> None:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.self_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            await self.smtp_session.send_message(msg)

        except aiosmtplib.SMTPRecipientsRefused as e:
            raise NonExistentEmail from e

        except Exception as e:
            self.logger.warning(e)
            raise e

    async def close(self) -> None:
        if self.smtp_session:
            self.smtp_session.close()
