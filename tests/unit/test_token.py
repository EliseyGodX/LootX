# flake8-in-file-ignores: noqa: WPS432

import logging
from datetime import timedelta

import pytest
from deepdiff import DeepDiff

from app.tokens.base import (BaseToken, JWToken, JWTokenConfig,
                             create_access_token, create_change_password_token,
                             create_delete_team_token, create_refresh_token,
                             create_registration_token, verify_access_token,
                             verify_change_password_token,
                             verify_delete_team_token, verify_refresh_token,
                             verify_registration_token)
from app.tokens.configs import BaseTokenConfig

parametrize = {
    'argnames': 'token_type, config',
    'argvalues': [
        [
            JWToken,
            JWTokenConfig(
                logger=logging.getLogger('token'),
                alg='HS256',  # type: ignore
                typ='JWT',
                key='SECRET_KEY'
            )
        ]
    ]
}


@pytest.mark.parametrize(**parametrize)
@pytest.mark.asyncio
async def test_access_token(
    token_type: type[BaseToken], config: BaseTokenConfig
) -> None:
    token = create_access_token(
        token_type=token_type,
        token_config=config,
        exp=timedelta(hours=12),
        sub='test_user'
    )
    verify_token = verify_access_token(
        token=token.encode(),
        token_type=token_type,
        token_config=config
    )
    diff = DeepDiff(
        token.payload.model_dump(),
        verify_token.payload.model_dump()
    )
    assert not diff, diff


@pytest.mark.parametrize(**parametrize)
@pytest.mark.asyncio
async def test_refresh_token(
    token_type: type[BaseToken], config: BaseTokenConfig
) -> None:
    token = create_refresh_token(
        token_type=token_type,
        token_config=config,
        exp=timedelta(hours=12),
        sub='test_user'
    )
    verify_token = verify_refresh_token(
        token=token.encode(),
        token_type=token_type,
        token_config=config
    )
    diff = DeepDiff(
        token.payload.model_dump(),
        verify_token.payload.model_dump()
    )
    assert not diff, diff


@pytest.mark.parametrize(**parametrize)
@pytest.mark.asyncio
async def test_registration_token(
    token_type: type[BaseToken], config: BaseTokenConfig
) -> None:
    token = create_registration_token(
        token_type=token_type,
        token_config=config,
        exp=timedelta(hours=12),
        sub='test_user'
    )
    verify_token = verify_registration_token(
        token=token.encode(),
        token_type=token_type,
        token_config=config
    )
    diff = DeepDiff(
        token.payload.model_dump(),
        verify_token.payload.model_dump()
    )
    assert not diff, diff


@pytest.mark.parametrize(**parametrize)
@pytest.mark.asyncio
async def test_change_password_token(
    token_type: type[BaseToken], config: BaseTokenConfig
) -> None:
    token = create_change_password_token(
        token_type=token_type,
        token_config=config,
        exp=timedelta(hours=12),
        sub='test_user'
    )
    verify_token = verify_change_password_token(
        token=token.encode(),
        token_type=token_type,
        token_config=config
    )
    diff = DeepDiff(
        token.payload.model_dump(),
        verify_token.payload.model_dump()
    )
    assert not diff, diff


@pytest.mark.parametrize(**parametrize)
@pytest.mark.asyncio
async def test_delete_team_token(
    token_type: type[BaseToken], config: BaseTokenConfig
) -> None:
    token = create_delete_team_token(
        token_type=token_type,
        token_config=config,
        exp=timedelta(hours=12),
        sub='test_user'
    )
    verify_token = verify_delete_team_token(
        token=token.encode(),
        token_type=token_type,
        token_config=config
    )
    diff = DeepDiff(
        token.payload.model_dump(),
        verify_token.payload.model_dump()
    )
    assert not diff, diff
