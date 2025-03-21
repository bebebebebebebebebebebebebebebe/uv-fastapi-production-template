import asyncio
import random
import string
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from typing import Any

import freezegun
import pytest
import pytest_asyncio
from faker import Faker
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from src.app.api.v1.users.schemas import DataInUser
from src.app.core.config import settings
from src.app.core.db.database import get_db_async
from src.app.crud.user_crud import UserCRUD
from src.app.main import app
from src.app.models.base_model import Base
from src.app.schemas.user_schemas import CreateInternalUser, ReadUser
from src.app.services.user_service import get_hashed_password
from src.utils.logger import get_logger

sync_engine = create_engine(settings.postgres_sync_uri, echo=True)
sync_session_local = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
logger = get_logger(__name__)


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    base_url = 'https://testserver'
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        yield client


@pytest.fixture
def get_test_db() -> Generator[Session, Any, None]:
    Base.metadata.create_all(bind=sync_engine)

    try:
        db = sync_session_local()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=sync_engine)


@pytest_asyncio.fixture(scope='session')
async def async_test_engine():
    async_engine = create_async_engine(settings.postgres_async_uri, echo=False)
    yield async_engine
    await async_engine.dispose()


@pytest_asyncio.fixture(scope='session')
async def get_test_db_async(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_local = sessionmaker(class_=AsyncSession, autocommit=False, autoflush=False, bind=async_test_engine)
    async with async_session_local() as db:
        async with async_test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()
            async with async_test_engine.begin() as conn:
                logger.info('Dropping all tables')
                await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def override_get_db_async(get_test_db_async: AsyncSession):
    app.dependency_overrides[get_db_async] = lambda: get_test_db_async
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def data_in_user() -> DataInUser:
    faker = Faker()
    faker.seed_instance(4321)
    user_data_json = {
        'name': faker.name(),
        'username': faker.user_name(),
        'email': faker.email(),
        'password': faker.password(),
    }
    return DataInUser(**user_data_json)


@pytest_asyncio.fixture
async def create_user(get_test_db_async: AsyncSession, data_in_user: DataInUser, override_get_db_async) -> tuple[ReadUser, DataInUser]:
    user_crud = UserCRUD(get_test_db_async)
    existing_user = await user_crud.get_by_email_async(data_in_user.email)
    if existing_user:
        logger.info(f'User with email {data_in_user.email} already exists.')
        return existing_user, data_in_user

    logger.info(f'Registering user with email {data_in_user.email}.')
    user_data = CreateInternalUser(
        name=data_in_user.name,
        username=data_in_user.username,
        email=data_in_user.email,
        hashed_password=get_hashed_password(data_in_user.password),
    )
    await user_crud.create_async(user_data)
    await get_test_db_async.commit()
    assert await user_crud.email_exists_async(data_in_user.email)
    user_data = await user_crud.get_by_email_async(data_in_user.email)
    assert user_data is not None
    return user_data, data_in_user


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, create_user: tuple[ReadUser, DataInUser]):
    if client.headers.get('Authorization') is not None:
        logger.info('Client is already authenticated')
        return client

    _, in_data = create_user

    login_user = {
        'username': in_data.email,
        'password': in_data.password,
    }
    response = await client.post('/api/v1/auth/login', data=login_user)
    assert response.status_code == status.HTTP_200_OK
    access_token = response.json()['access_token']
    client.headers['Authorization'] = f'Bearer {access_token}'
    if not response.cookies.get('refresh_token'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='refresh_tokenが取得できませんでした。',
        )
    if not client.cookies.get('refresh_token'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='refresh_tokenがクライアントから取得できませんでした。',
        )
    return client


@pytest.fixture
def random_password(request):
    # request.param が指定されていない場合のデフォルト値を辞書で定義
    params = request.param if hasattr(request, 'param') else {}
    length = params.get('length', 12)
    include_uppercase = params.get('include_uppercase', True)
    include_lowercase = params.get('include_lowercase', True)
    include_digits = params.get('include_digits', True)
    include_special = params.get('include_special', True)
    min_uppercase = params.get('min_uppercase', 1)
    min_lowercase = params.get('min_lowercase', 1)
    min_digits = params.get('min_digits', 1)
    min_special = params.get('min_special', 0)

    logger.info(
        f'Generating random password with length {length}, including uppercase: {include_uppercase}, '
        f'lowercase: {include_lowercase}, digits: {include_digits}, special: {include_special}, '
        f'min_uppercase: {min_uppercase}, min_lowercase: {min_lowercase}, min_digits: {min_digits}, '
        f'min_special: {min_special}'
    )

    # バリデーション
    min_required_chars = min_uppercase + min_lowercase + min_digits + min_special
    if length < min_required_chars:
        raise ValueError(f'パスワードの長さ({length})が最低必要文字数({min_required_chars})より短いです')

    # 文字種ごとのプールを用意
    char_pools = []
    required_chars = []

    if include_uppercase:
        char_pools.append(string.ascii_uppercase)
        required_chars.extend(random.choices(string.ascii_uppercase, k=min_uppercase))

    if include_lowercase:
        char_pools.append(string.ascii_lowercase)
        required_chars.extend(random.choices(string.ascii_lowercase, k=min_lowercase))

    if include_digits:
        char_pools.append(string.digits)
        required_chars.extend(random.choices(string.digits, k=min_digits))

    if include_special:
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        char_pools.append(special_chars)
        required_chars.extend(random.choices(special_chars, k=min_special))

    if not char_pools:
        raise ValueError('少なくとも1つの文字種を含める必要があります')

    # 残りの文字を必要な長さまで生成
    all_chars = ''.join(char_pools)
    remaining_length = length - len(required_chars)

    if remaining_length > 0:
        remaining_chars = [random.choice(all_chars) for _ in range(remaining_length)]
        password_chars = required_chars + remaining_chars
    else:
        password_chars = required_chars[:length]  # 必要な文字だけで十分な場合

    # 順番をシャッフル
    random.shuffle(password_chars)

    return ''.join(password_chars)


@pytest.fixture
def random_valid_password(random_password) -> str:
    """
    大文字、小文字、数字を含むランダムなパスワードを生成するフィクスチャー
    (パラメータ化フィクスチャー用)
    """
    return random_password


@pytest.fixture
def fixed_time():
    with freezegun.freeze_time('2023-01-01 00:00:00'):
        yield datetime(2023, 1, 1, 0, 0, 0) + timedelta(seconds=settings.DIFFERENCE_TIMESTAMP_JST)


@pytest.fixture
def fixed_time_with_out_timezone():
    with freezegun.freeze_time('2023-01-01 00:00:00'):
        yield datetime(2023, 1, 1, 0, 0, 0)
