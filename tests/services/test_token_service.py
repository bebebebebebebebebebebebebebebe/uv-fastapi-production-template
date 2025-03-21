from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from faker import Faker
from jose import jwt
from src.app.core.config import settings
from src.app.schemas.token_schemas import TokenUserData
from src.app.services.token_service import token_service


@pytest.fixture
def user_payload():
    faker = Faker()
    faker.seed_instance(4422)
    token_user_data = {
        'id': faker.random_int(min=1, max=1000),
        'email': faker.email(),
        'role': 'user',
    }
    return TokenUserData(**token_user_data)


def test_create_access_token(user_payload):
    access_token = token_service.create_access_token(user_payload)
    decoded_token = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded_token['sub'] == str(user_payload.id)
    assert decoded_token['token_type'] == 'access'
    assert 'exp' in decoded_token


def test_create_refresh_token(user_payload):
    refresh_token = token_service.create_refresh_token(user_payload)
    decoded_token = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded_token['sub'] == str(user_payload.id)
    assert decoded_token['token_type'] == 'refresh'
    assert 'exp' in decoded_token


def test_verify_access_token(user_payload):
    token = token_service.create_access_token(user_payload)
    verified_data = token_service.verify_token(token)
    assert verified_data.id == str(user_payload.id)
    assert verified_data.email == user_payload.email
    assert verified_data.role == user_payload.role
    assert verified_data.token_type == 'access'
    assert verified_data.exp > datetime.now(tz=ZoneInfo('Asia/Tokyo'))


def test_verify_token_by_email(user_payload):
    email_token = token_service.create_email_verification_token(user_payload)
    payload = token_service.verify_token(email_token)
    assert payload.id == str(user_payload.id)
    assert payload.email == user_payload.email
    assert payload.token_type == 'email_verification'
    assert payload.exp > datetime.now(tz=ZoneInfo('Asia/Tokyo'))


def test_verify_invalid_secretkey(user_payload: TokenUserData, random_password):
    wrong_secret_key = random_password
    invalid_token = jwt.encode(
        {'sub': str(user_payload.id), 'token_type': 'access'},
        wrong_secret_key,
        algorithm=settings.ALGORITHM,
    )
    verified_data = token_service.verify_token(invalid_token)
    assert verified_data is None


def test_verify_invalid_token(user_payload):
    invalid_token = 'invalid_token'
    verified_data = token_service.verify_token(invalid_token)
    assert verified_data is None


def test_verify_expired_token(user_payload):
    # 有効期限が切れているトークンを検証
    expired_token = token_service.create_access_token(user_payload, expires_delta=timedelta(seconds=-1))
    verified_data = token_service.verify_token(expired_token)
    assert verified_data is None
