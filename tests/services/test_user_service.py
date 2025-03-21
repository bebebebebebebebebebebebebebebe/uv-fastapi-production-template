import pytest
from src.app.services.user_service import get_hashed_password, verify_password
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def password(random_valid_password):
    return random_valid_password


@pytest.fixture
def test_get_hashed_password(password):
    hashed_password = get_hashed_password(password)
    logger.info(f'Password: {password}')
    logger.info(f'Hashed password: {hashed_password}')
    assert len(hashed_password) > 0


def test_verify_password(password):
    hashed_password = get_hashed_password(password)
    is_valid = verify_password(password, hashed_password)
    logger.info('Password: %s is verified: %s', password, is_valid)
    assert is_valid
