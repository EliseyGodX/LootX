# flake8-in-file-ignores: noqa: WPS432

import asyncio
import logging
from datetime import timedelta
from typing import Any, Callable, Coroutine

import pytest
from kapusta import AlchemyCRUD
from testcontainers.core.generic import DbContainer
from testcontainers.postgres import PostgresContainer

from app.db.abc.base import BaseAsyncDB
from app.db.exc import UserNotFoundError
from app.db.sqlalchemy.base import AsyncSQLAlchemyDB
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
from app.task_managers.base import (BaseAsyncTaskManager, KapustaTaskManager,
                                    Tasks)
from app.task_managers.configs import BaseTaskManagerConfig, KapustaConfig
from app.types import UserId

db_type = AsyncSQLAlchemyDB
db_config = SQLAlchemyDBConfig(
    logger=logging.getLogger('db'),
    db_url='',
    session_maker_kwargs={'expire_on_commit': False}
)


def del_inactive_user_task(db: BaseAsyncDB) -> Callable[..., Coroutine[Any, Any, None]]:
    async def wrapper(user_id: UserId) -> None:
        if not await db.is_user_active(user_id):
            await db.del_user(user_id)
    return wrapper


def update_config(config: BaseTaskManagerConfig, testcontainer: DbContainer) -> None:
    config_type = type(config)
    if config_type == KapustaConfig:
        config.crud = AlchemyCRUD(testcontainer.get_connection_url())  # type: ignore


@pytest.mark.parametrize(
    argnames='task_manager_type, config, testcontainer',
    argvalues=[
        [
            KapustaTaskManager,
            KapustaConfig(
                logger=logging.getLogger('kapusta'),
                crud=AlchemyCRUD(''),
                max_tick_interval=1,
                default_overdue_time_delta=None,
                default_max_retry_attempts=3,
                default_timeout=0
            ),
            PostgresContainer(
                dbname='lootx',
                driver='asyncpg'
            )
        ]
    ]
)
@pytest.mark.asyncio
async def test_task_manager(
    task_manager_type: type[BaseAsyncTaskManager], config: BaseTaskManagerConfig,
    testcontainer: DbContainer
) -> None:
    with testcontainer as container:
        db_config.db_url = container.get_connection_url()
        db = db_type(db_config)

        update_config(config, container)
        task_manager = task_manager_type(
            config,
            Tasks(
                del_inactive_user=del_inactive_user_task(db)
            )
        )

        await db.connect()
        await task_manager.connect()

        user = await db.create_user(
            username=task_manager_type.__name__[:12],
            password='password',
            email='task_manager_test@mail.com',
            is_active=False
        )
        await task_manager.del_inactive_user(
            user_id=user.id,
            eta_delta=timedelta(seconds=0)
        )
        await asyncio.sleep(3)
        with pytest.raises(UserNotFoundError):
            user = await db.get_user(user.id)

        await task_manager.close()
        await db.close()
