# flake8-in-file-ignores: noqa: WPS204, WPS218

import json
import logging
from typing import AsyncGenerator, Sequence, TypedDict

import pytest
import pytest_asyncio
from deepdiff import DeepDiff
from pytest_mock import MockerFixture
from testcontainers.core.generic import DbContainer
from testcontainers.postgres import PostgresContainer

from app.db.abc.base import BaseAsyncDB
from app.db.abc.configs import BaseDBConfig
from app.db.abc.models import (LogProtocol, QueueProtocol, RaiderProtocol,
                               TeamProtocol, UserProtocol, WoWItemProtocol)
from app.db.enums import EnumAddons, EnumClasses, EnumLanguages
from app.db.exc import (InvalidCredentialsError, TeamsNotExistsError,
                        UniqueEmailError, UniqueUsernameError,
                        UserNotFoundError)
from app.db.sqlalchemy.base import AsyncSQLAlchemyDB
from app.db.sqlalchemy.config import SQLAlchemyDBConfig
from app.db.wow_api.base import BaseAsyncWoWAPI, WoWHeadAPI
from app.db.wow_api.configs import BaseWoWAPIConfig, WoWHeadAPIConfig


class RequestDBParam(TypedDict):
    db_type: type[BaseAsyncDB]
    config: BaseDBConfig
    testcontainer: DbContainer


class RequestWoWAPIParam(TypedDict):
    wow_api_type: type[BaseAsyncWoWAPI]
    config: BaseWoWAPIConfig


@pytest.fixture
def full_team_dump() -> dict:
    with open('tests/unit/full_team_dump.json', 'r', encoding='utf-8') as dump:
        return json.load(dump)


@pytest.fixture(scope='module')
def wow_items_id() -> list[int]:
    return [
        16541, 16542, 16543,
        16544, 16545, 165458
    ]


@pytest_asyncio.fixture(params=[
    {
        'db_type': AsyncSQLAlchemyDB,
        'config': SQLAlchemyDBConfig(
            logger=logging.getLogger('db'),
            db_url='',
            session_maker_kwargs={'expire_on_commit': False}
        ),
        'testcontainer': PostgresContainer(
            dbname='lootx',
            driver='asyncpg'
        )
    }
], scope='module')
async def db(
    request: pytest.FixtureRequest
) -> AsyncGenerator[BaseAsyncDB, None]:
    request_param: RequestDBParam = request.param
    with request_param['testcontainer'] as container:
        request_param['config'].db_url = container.get_connection_url()
        db = request_param['db_type'](request_param['config'])
        await db.connect()
        yield db
        await db.close()


@pytest_asyncio.fixture(params=[
    {
        'wow_api_type': WoWHeadAPI,
        'config': WoWHeadAPIConfig(
            logger=logging.getLogger('wow_head'),
            url='https://www.wowhead.com/{addon}/{lang}/item={id}&xml',
            icon_url='https://wow.zamimg.com/images/wow/icons/large/{icon}.jpg'
        )
    }
], scope='module')
async def wow_api(
    request: pytest.FixtureRequest
) -> AsyncGenerator[BaseAsyncWoWAPI, None]:
    request_param: RequestWoWAPIParam = request.param
    wow_api = request_param['wow_api_type'](
        request_param['config']
    )
    await wow_api.connect()
    yield wow_api
    await wow_api.close()


def check_user(user: UserProtocol, second_user: UserProtocol) -> None:
    assert user.id == second_user.id
    assert user.username == second_user.username
    assert user.password == second_user.password
    assert user.email == second_user.email
    assert user.is_active is second_user.is_active


def check_team(team: TeamProtocol, second_team: TeamProtocol) -> None:
    assert team.id == second_team.id
    assert team.name == second_team.name
    assert team.addon == second_team.addon
    assert team.owner_id == second_team.owner_id
    assert team.password == second_team.password


def check_raider(raider: RaiderProtocol, second_raider: RaiderProtocol) -> None:
    assert raider.id == second_raider.id
    assert raider.name == second_raider.name
    assert raider.class_name == second_raider.class_name
    assert raider.is_active == second_raider.is_active


def check_wow_item(
    wow_item: WoWItemProtocol, second_wow_item: WoWItemProtocol
) -> None:
    assert wow_item.id == second_wow_item.id
    assert wow_item.addon == second_wow_item.addon
    assert wow_item.html_tooltip == second_wow_item.html_tooltip
    assert wow_item.icon_url == second_wow_item.icon_url
    assert wow_item.lang == second_wow_item.lang
    assert wow_item.origin_link == second_wow_item.origin_link
    assert wow_item.wow_id == second_wow_item.wow_id


def check_queue(
    queue: Sequence[QueueProtocol], second_queue: Sequence[QueueProtocol]
) -> None:
    assert len(queue) == len(second_queue)
    for i in range(len(queue)):  # noqa: WPS518
        assert queue[i].id == second_queue[i].id
        assert queue[i].position == second_queue[i].position
        assert queue[i].raider_id == second_queue[i].raider_id
        assert queue[i].team_id == second_queue[i].team_id
        assert queue[i].wow_item_id == second_queue[i].wow_item_id


def check_log(
    log: LogProtocol, second_log: LogProtocol
) -> None:
    assert log.id == second_log.id
    assert log.created_at == second_log.created_at
    assert log.queue == second_log.queue
    assert log.team_id == second_log.team_id
    assert log.user_id == second_log.user_id
    assert log.wow_item_id == second_log.wow_item_id


@pytest.mark.asyncio
async def test_user_model(db: BaseAsyncDB) -> None:

    # Method: create_user
    user = await db.create_user(
        username='username',
        password='password',
        email='email@mail.com',
        is_active=False
    )
    assert user.username == 'username'
    assert user.password != 'password'
    assert user.email == 'email@mail.com'
    assert user.is_active is False

    # Method: get_user
    check_user(user, await db.get_user(user.id))

    # Method: get_user, get_user_by_username
    check_user(user, await db.get_user_by_username(user.username))

    # Method: get_user_email
    assert await db.get_user_email(user.id) == user.email

    # Method: is_user_username_email_unique
    assert await db.is_user_username_email_unique(
        username='unique', email='unique'
    ) is True
    with pytest.raises((UniqueUsernameError, UniqueEmailError)):
        await db.is_user_username_email_unique(
            username=user.username, email=user.email
        )
    with pytest.raises(UniqueUsernameError):
        await db.is_user_username_email_unique(
            username=user.username, email='unique'
        )
    with pytest.raises(UniqueEmailError):
        await db.is_user_username_email_unique(
            username='unique', email=user.email
        )

    # Method: change_user_password
    old_password = user.password
    await db.change_user_password(user.id, 'newpassword')
    user = await db.get_user(user.id)
    assert user.password != old_password, 'Password should be changed'
    assert user.password != 'newpassword', 'The password is not hashed'

    # Method: is_user_active
    assert await db.is_user_active(user.id) is False, \
        'Expected user to be not active'

    # Method: activate_user
    await db.activate_user(user.username)
    user = await db.get_user(user.id)
    assert user.is_active is True, 'Expected user to be active after activation'

    # Method: verify_username_password
    assert await db.verify_username_password(
        username=user.username, password='newpassword'
    ) == user.id
    with pytest.raises(InvalidCredentialsError):
        await db.verify_username_password(
            username=user.username, password='invalid_password'
        )

    # Method: del_user
    await db.del_user(user.id)
    with pytest.raises(UserNotFoundError):
        user = await db.get_user(user.id)


@pytest.mark.asyncio
async def test_team_model(db: BaseAsyncDB) -> None:
    user = await db.create_user(
        username='team_user',
        password='password',
        email='test_team_user@mail.com',
        is_active=True
    )

    # Method: create_team
    team = await db.create_team(
        name='name',
        addon=EnumAddons.retail,
        owner_id=user.id,
        password='password'
    )
    assert team.name == 'name'
    assert team.addon == EnumAddons.retail
    assert team.owner_id == user.id
    assert team.password != 'password', 'The password is not hashed'

    # Method: get_team
    check_team(team, await db.get_team(team.id))

    # Method: get_team_by_name
    check_team(team, await db.get_team_by_name(team.name))

    # Method: get_team_with_owner
    team_with_owner = await db.get_team_with_owner(team.id)
    check_team(team, team_with_owner)
    check_user(user, team_with_owner.owner)

    # Method: get_team_by_name_with_owner
    team_by_name_with_owner = await db.get_team_by_name_with_owner(team.name)
    check_team(team, team_by_name_with_owner)
    check_user(user, team_by_name_with_owner.owner)

    # Method: get_team_id_by_name
    assert await db.get_team_id_by_name(team.name) == team.id

    # Method: update_team
    old_password = team.password
    team = await db.update_team(
        id=team.id,
        name='update_name',
        addon=EnumAddons.classic,
        password='update_password'
    )
    assert team.name == 'update_name'
    assert team.addon == EnumAddons.classic
    assert team.password != 'update_password', 'The password is not hashed'
    assert team.password != old_password

    # Method: del_team
    await db.del_team(team.id)
    with pytest.raises(TeamsNotExistsError):
        team = await db.get_team(team.id)


@pytest.mark.asyncio
async def test_raider_model(db: BaseAsyncDB) -> None:
    user = await db.create_user(
        username='raider_user',
        password='password',
        email='test_raider_user@mail.com',
        is_active=True
    )
    team = await db.create_team(
        name='raider_team',
        addon=EnumAddons.retail,
        owner_id=user.id,
        password='password'
    )

    # Method: create_raider
    raider = await db.create_raider(
        name='name',
        team_id=team.id,
        class_name=EnumClasses.warrior
    )
    assert raider.name == 'name'
    assert raider.team_id == team.id
    assert raider.class_name == EnumClasses.warrior

    # Method: get_raider
    check_raider(raider, await db.get_raider(raider.id))

    # Method: set_raider_inactive
    await db.set_raider_inactive(raider.id)
    raider = await db.get_raider(raider.id)
    assert raider.is_active is False


@pytest.mark.asyncio
async def test_queue_model(
    db: BaseAsyncDB, wow_api: BaseAsyncWoWAPI, wow_items_id: list[int]
) -> None:
    user = await db.create_user(
        username='queue_user',
        password='password',
        email='test_queue_user@mail.com',
        is_active=True
    )
    team = await db.create_team(
        name='queue_team',
        addon=EnumAddons.retail,
        owner_id=user.id,
        password='password'
    )
    raider = await db.create_raider(
        name='queue_raider',
        team_id=team.id,
        class_name=EnumClasses.warrior
    )

    # Method: create_queue
    queue = await db.create_queue(
        team_id=team.id,
        wow_item_id=wow_items_id[0],
        addon=EnumAddons.retail,
        lang=EnumLanguages.en,
        raiders=[raider.id],
        wow_api=wow_api
    )
    assert queue[0].position == 1
    assert queue[0].team_id == team.id
    assert queue[0].raider_id == raider.id
    assert queue[0].wow_item_id == wow_items_id[0]

    # Method: get_queue_by_item
    check_queue(queue, await db.get_queue_by_item(
        team_id=queue[0].team_id, wow_item_id=queue[0].wow_item_id
    ))

    # Method: get_queues
    check_queue(
        queue,
        (await db.get_queues(queue[0].team_id))[0]
    )

    # Method: is_queue_exists
    assert await db.is_queue_exists(
        team_id=queue[0].team_id,
        wow_item_id=queue[0].wow_item_id
    )
    assert not await db.is_queue_exists(
        team_id='',
        wow_item_id=queue[0].wow_item_id
    )
    assert not await db.is_queue_exists(
        team_id=queue[0].team_id,
        wow_item_id=0
    )
    assert not await db.is_queue_exists(
        team_id='',
        wow_item_id=0
    )

    # Method: del_queue
    await db.del_queue(
        team_id=queue[0].team_id, wow_item_id=queue[0].wow_item_id
    )
    assert not await db.is_queue_exists(
        team_id=queue[0].team_id,
        wow_item_id=queue[0].wow_item_id
    )


@pytest.mark.asyncio
async def test_log_model(
    db: BaseAsyncDB, wow_items_id: list[int]
) -> None:
    user = await db.create_user(
        username='log_user',
        password='password',
        email='test_log_user@mail.com',
        is_active=True
    )
    team = await db.create_team(
        name='log_team',
        addon=EnumAddons.retail,
        owner_id=user.id,
        password='password'
    )

    # Method: create_log
    log = await db.create_log(
        team_id=team.id,
        user_id=user.id,
        wow_item_id=wow_items_id[0],
        queue=''
    )
    assert log.team_id == team.id
    assert log.user_id == user.id
    assert log.wow_item_id == wow_items_id[0]
    assert log.queue == ''

    # Method: get_logs
    check_log(
        log,
        (await db.get_logs(team_id=log.team_id, wow_item_id=log.wow_item_id))[0]
    )


@pytest.mark.asyncio
async def test_wow_item_model(
    db: BaseAsyncDB, wow_api: BaseAsyncWoWAPI, wow_items_id: list[int],
    mocker: MockerFixture
) -> None:

    # Method: get_wow_item_by_wow_id
    wow_item = await db.get_wow_item_by_wow_id(
        wow_id=wow_items_id[0],
        addon=EnumAddons.classic,
        lang=EnumLanguages.en,
        wow_api=wow_api
    )
    assert wow_item is not None
    assert wow_item.wow_id == wow_items_id[0]
    # The record should be taken from the database if it exists
    mock_wow_api = mocker.Mock(spec=BaseAsyncWoWAPI)
    mock_wow_api.get_item = mocker.AsyncMock()
    wow_item = await db.get_wow_item_by_wow_id(
        wow_id=wow_items_id[0],
        addon=EnumAddons.classic,
        lang=EnumLanguages.en,
        wow_api=mock_wow_api,
    )
    assert wow_item is not None
    assert wow_item.wow_id == wow_items_id[0]
    mock_wow_api.get_item.assert_not_called()

    # Method: get_wow_item
    check_wow_item(wow_item, await db.get_wow_item(wow_item.id))


@pytest.mark.asyncio
async def test_full_team(
    db: BaseAsyncDB, wow_api: BaseAsyncWoWAPI, wow_items_id: list[int],
    full_team_dump: dict
) -> None:
    user = await db.create_user(
        username='full_team',
        password='password',
        email='test_full_team@mail.com',
        is_active=True
    )

    team = await db.create_team(
        name='full_team',
        addon=EnumAddons.retail,
        owner_id=user.id,
        password='password'
    )

    raiders = []
    for i, class_name in enumerate(EnumClasses):
        raiders.append((await db.create_raider(
            name=str(i),
            team_id=team.id,
            class_name=class_name
        )).id)

    for item_id in wow_items_id:
        await db.create_queue(
            team_id=team.id,
            wow_item_id=item_id,
            addon=EnumAddons.retail,
            lang=EnumLanguages.en,
            raiders=raiders,
            wow_api=wow_api
        )
        raiders.pop()
        if len(raiders) == 0:
            break

    team, queues = await db.get_full_team(team.id)
    full_team = {
        'team': {
            'name': team.name,
            'addon': team.addon.value,
        },
        'queues': [
            {
                'wow_item_id': queue[0].wow_item_id,
                'queue': [
                    {
                        'position': index.position,
                        'raider': {
                            'name': index.raider.name,
                            'class_name': index.raider.class_name.value,
                            'is_active': index.raider.is_active
                        },
                    } for index in queue
                ]
            } for queue in queues
        ]
    }

    diff = DeepDiff(full_team, full_team_dump)
    assert not diff, diff
