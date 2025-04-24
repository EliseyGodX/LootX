# flake8-in-file-ignores: noqa: WPS432

import logging

import httpx
import pytest
from testcontainers.mailpit import MailpitContainer

from app.mailers.base import AsyncSMTPMailer, BaseAsyncMailer
from app.mailers.configs import BaseMailerConfig, SMTPConfig


def update_config(config: BaseMailerConfig, testcontainer: MailpitContainer) -> None:
    config_type = type(config)
    if config_type == SMTPConfig:
        config.smtp_server = testcontainer.get_container_host_ip()  # type: ignore
        config.smtp_port = testcontainer.get_exposed_smtp_port()  # type: ignore


@pytest.mark.parametrize(
    argnames='mailer_type, config',
    argvalues=[
        [
            AsyncSMTPMailer,
            SMTPConfig(
                logger=logging.getLogger('mailer'),
                self_email='test@mail.com',
                smtp_user='',
                smtp_password='',
                smtp_server='',
                smtp_port=0
            )
        ]
    ]
)
@pytest.mark.asyncio
async def test_smtp_mailer(
    mailer_type: type[BaseAsyncMailer], config: BaseMailerConfig,
) -> None:
    with MailpitContainer() as mailpit:
        update_config(config, mailpit)
        mailer = mailer_type(config)
        await mailer.connect()

        await mailer.send(
            subject='test_subject',
            body='test_body',
            to_email='to_test_email@mail.com'
        )
        async with httpx.AsyncClient() as client:
            smtp_response = await client.get((
                'http://' + mailpit.get_container_host_ip()
                + ':' + str(mailpit.get_exposed_port(8025))
                + '/api/v1/messages'
            ))
        message = smtp_response.json()['messages'][0]

        assert message['From']['Address'] == 'test@mail.com'
        assert message['To'][0]['Address'] == 'to_test_email@mail.com'
        assert message['Subject'] == 'test_subject'
        assert message['Snippet'] == 'test_body'

        await mailer.close()
