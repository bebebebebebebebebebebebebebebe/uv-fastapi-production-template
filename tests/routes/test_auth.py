from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx
from google.oauth2 import id_token
from src.app.api.v1.users.schemas import DataInUser
from src.app.core.config import settings
from src.app.crud.social_account_crud import SocialAccountCRUD
from src.app.crud.user_crud import UserCRUD
from src.app.schemas.social_account_schema import ReadSocialAccount
from src.app.schemas.token_schemas import TokenUserData
from src.app.schemas.user_schemas import CreateInternalUser, ReadUser
from src.app.services.token_service import JWTTokenService, token_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def dummy_token_data():
    return {
        'id_token': 'dummy_id_token',
        'access_token': 'dummy_access_token',
        'refresh_token': 'dummy_refresh_token',
        'expires_in': 3600,
    }


@pytest.fixture
def dummy_verify_oauth2_token():
    return {
        'sub': 'dummy_google_user_id',
        'email': 'dummy@example.com',
        'name': 'Dummy User',
        'email_verified': True,
        'exp': int(datetime.now(tz=ZoneInfo('Asia/Tokyo')).timestamp() + 3600),
        'picture': 'http://example.com/dummy.png',
    }


@pytest.mark.asyncio
async def test_login(client: httpx.AsyncClient, create_user: tuple[ReadUser, DataInUser]):
    _, register_user = create_user
    login_user = {
        'username': register_user.email,
        'password': register_user.password,
    }
    response = await client.post('/api/v1/auth/login', data=login_user)
    result = response.json()
    logger.info('Test login response: %s', result)
    assert response.status_code == 200
    assert result.get('access_token') is not None
    assert result.get('token_type') == 'bearer'
    assert response.cookies.get('refresh_token') is not None


@pytest.mark.asyncio
async def test_logout(authed_client: httpx.AsyncClient):
    response = await authed_client.post('/api/v1/auth/logout')
    logger.info('Client cookies before logout: %s', authed_client.cookies.jar)
    result = response.json()
    logger.info('Test logout response: %s', result)
    assert response.status_code == 200
    assert result == {'message': 'Successfully logged out'}
    assert authed_client.cookies.get('refresh_token') is None


@pytest.mark.asyncio
async def test_verify_email(authed_client: httpx.AsyncClient):
    current_user_response = await authed_client.get('/api/v1/users/me')
    current_user = ReadUser(**current_user_response.json())
    token_data = TokenUserData(
        id=current_user.id,
        email=current_user.email,
    )
    token = token_service.create_email_verification_token(data=token_data)
    response = await authed_client.get(f'/api/v1/auth/verify-email?token={token}')
    result = response.json()
    logger.info('Test verify email response: %s', result)
    assert response.status_code == 200
    assert result == {'message': 'Email verified successfully'}


@pytest.mark.skip
async def test_login_with_google(client: httpx.AsyncClient):
    response = await client.get('/api/v1/auth/google/login')
    assert response.status_code == 307
    expected_url = (
        f'{settings.GOOGLE_AUTH_URL}'
        f'?client_id={settings.GOOGLE_OAUTH_CLIENT_ID}'
        f'&redirect_uri={settings.get_google_redirect_uri}'
        f'&response_type=code'
        f'&scope=openid%20email%20profile'
        f'&access_type=offline'
        f'&prompt=consent'
    )
    assert response.headers['location'] == expected_url


@pytest.mark.asyncio
async def test_login_with_google_callback(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch, dummy_token_data: dict, dummy_verify_oauth2_token
):
    # DB 関連の CRUD をダミー関数に置換して、新規ユーザー作成が行われるシナリオとする
    async def dummy_get_by_provider_and_id(self, provider_user_id, provider):
        # 存在しないものとする
        return None

    async def get_by_email_async(self, email):
        return None

    async def username_exists_async(self, username):
        return False

    async def create_user_async(self, obj_in: CreateInternalUser):
        return ReadUser(
            id=1,
            name=dummy_verify_oauth2_token['name'],
            username=dummy_verify_oauth2_token['email'] + '_google',
            email=dummy_verify_oauth2_token['email'],
            is_active=True,
            is_superuser=False,
            is_verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def create_social_account_async(self, obj_in: CreateInternalUser):
        return ReadSocialAccount(
            id=1,
            user_id=1,
            provider='google',
            provider_email=dummy_verify_oauth2_token['email'],
            provider_user_id=dummy_verify_oauth2_token['sub'],
            token_expiry=datetime.now(tz=ZoneInfo('Asia/Tokyo')) + timedelta(seconds=3600),
            created_at=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
        )

    with respx.mock:
        respx.post(settings.GOOGLE_TOKEN_URL).mock(
            return_value=httpx.Response(
                status_code=200,
                json=dummy_token_data,
            )
        )
        monkeypatch.setattr(id_token, 'verify_oauth2_token', lambda *args, **kwargs: dummy_verify_oauth2_token)

        monkeypatch.setattr(SocialAccountCRUD, 'get_by_provider_and_id', dummy_get_by_provider_and_id)
        monkeypatch.setattr(UserCRUD, 'get_by_email_async', get_by_email_async)
        monkeypatch.setattr(UserCRUD, 'username_exists_async', username_exists_async)
        monkeypatch.setattr(UserCRUD, 'create_async', create_user_async)
        monkeypatch.setattr(SocialAccountCRUD, 'create_async', create_social_account_async)

        monkeypatch.setattr(
            JWTTokenService,
            'create_access_token',
            lambda self, data, expires_delta: 'dummy_access_token',
        )
        monkeypatch.setattr(
            JWTTokenService,
            'create_refresh_token',
            lambda self, data, expires_delta: 'dummy_refresh_token',
        )

        response = await client.get(
            '/api/v1/auth/google/callback',
            params={
                'code': 'dummy_code',
            },
        )
        assert response.status_code in (302, 307)
