import pytest
from src.app.domains.users.schemas.user_schemas import Email, FullName, Password, ProfileImageURL
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def valid_password(random_valid_password):
    return random_valid_password


@pytest.mark.parametrize(
    'random_password',
    [{'length': 4, 'include_uppercase': False, 'include_lowercase': True, 'include_digits': True, 'include_special': False}],
    indirect=True,
)
@pytest.fixture
def invalid_password(random_password):
    return random_password


# --- FullName ---
def test_fullname_valid():
    fullname = FullName(first_name='John', last_name='Doe')
    assert str(fullname) == 'John Doe'


def test_fullname_extra_field_error():
    with pytest.raises(ValueError):
        FullName(first_name='John', last_name='Doe', middle_name='X')


# --- Email ---
def test_email_valid():
    valid_email = 'user@example.com'
    obj = Email(email=valid_email)
    assert obj.email == valid_email


def test_email_invalid():
    # 不正な形式のメールアドレス
    with pytest.raises(ValueError):
        Email(email='invalid-email')


def test_email_extra_field_error():
    # 余分なフィールド
    with pytest.raises(ValueError):
        Email(email='user@example.com', extra_field='not allowed')


# --- Password ---
def test_password_valid(valid_password):
    obj = Password(password=valid_password)
    assert obj.password == valid_password


@pytest.mark.parametrize(
    'random_password',
    [{'length': 4, 'include_uppercase': False, 'include_lowercase': True, 'include_digits': True, 'include_special': False}],
    indirect=True,
)
def test_password_invalid(invalid_password):
    # 7文字しかなく、大文字や記号も不足
    assert len(invalid_password) == 4
    logger.info(f'Invalid password: {invalid_password}')
    with pytest.raises(ValueError):
        Password(password=invalid_password)


def test_password_extra_field_error(valid_password):
    with pytest.raises(ValueError):
        Password(password=valid_password, extra='value')


# --- ProfileImageURL ---
def test_ProfileImageURL_valid():
    valid_url = 'https://example.com/path/to/image.jpg'
    pic = ProfileImageURL(profile_image_url=valid_url)
    assert pic.profile_image_url == valid_url


def test_ProfileImageURL_invalid_extension():
    invalid_url = 'https://example.com/path/to/image.txt'
    with pytest.raises(ValueError):
        ProfileImageURL(profile_image_url=invalid_url)


def test_ProfileImageURL_extra_field_error():
    valid_url = 'https://example.com/path/to/image.png'
    with pytest.raises(ValueError):
        ProfileImageURL(profile_image_url=valid_url, extra_field='not allowed')
