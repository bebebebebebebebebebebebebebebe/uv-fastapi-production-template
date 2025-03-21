import pytest
import pytest_asyncio
from faker import Faker
from src.app.api.v1.users.schemas import DataInUser
from src.app.crud.user_crud import UserCRUD
from src.app.schemas.user_schemas import CreateInternalUser
from src.app.services.user_service import get_hashed_password
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest_asyncio.fixture
def user_crud(get_test_db_async):
    return UserCRUD(get_test_db_async)


@pytest.fixture
def local_data_in_user():
    faker = Faker()
    faker.seed_instance(4322)
    return DataInUser(
        name=faker.name(),
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
    )


@pytest.mark.asyncio
async def test_register_user(local_data_in_user, user_crud: UserCRUD):
    register_user = CreateInternalUser(
        name=local_data_in_user.name,
        username=local_data_in_user.username,
        email=local_data_in_user.email,
        hashed_password=get_hashed_password(local_data_in_user.password),
    )
    result = await user_crud.create_async(register_user)
    assert result is not None
    assert result.id is not None
    assert await user_crud.email_exists_async(local_data_in_user.email)


@pytest.mark.asyncio
async def test_users_authenticate_async(user_crud: UserCRUD, local_data_in_user: DataInUser):
    login_user_email = local_data_in_user.email
    login_user_password = local_data_in_user.password
    result = await user_crud.authenticate(login_user_email, login_user_password)
    logger.info(f'result: {result}')
    assert result is not None


@pytest.mark.asyncio
async def test_update_verified(user_crud: UserCRUD, local_data_in_user: DataInUser):
    user = await user_crud.get_by_email_async(local_data_in_user.email)
    assert user is not None
    updated_user = await user_crud.update_verified(user.id)
    assert updated_user.is_verified is True
