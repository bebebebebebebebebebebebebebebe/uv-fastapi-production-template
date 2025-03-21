import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient
from src.app.api.v1.users.schemas import DataInUser
from src.app.crud.user_crud import UserCRUD
from src.app.schemas.user_schemas import ReadUser
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def local_data_in_user():
    faker = Faker()
    faker.seed_instance(4324)
    return DataInUser(
        name=faker.name(),
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
    )


@pytest.mark.asyncio
async def test_register_user(
    client: AsyncClient,
    local_data_in_user: DataInUser,
    get_test_db_async,
    override_get_db_async,
):
    response = await client.post('/api/v1/users/register', json=local_data_in_user.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    register_user = ReadUser(**response.json())
    assert register_user.name == local_data_in_user.name
    assert register_user.email == local_data_in_user.email
    crud_user = UserCRUD(get_test_db_async)
    assert await crud_user.email_exists_async(local_data_in_user.email)


@pytest.mark.asyncio
async def test_get_current_user(authed_client: AsyncClient):
    response = await authed_client.get('/api/v1/users/me')
    assert response.status_code == status.HTTP_200_OK
    user = ReadUser(**response.json())
    logger.info(f'user: {user}')
    assert user.email is not None
    assert user.name is not None
