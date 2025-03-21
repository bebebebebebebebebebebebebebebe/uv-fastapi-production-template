from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError
from src.app.domains.oauth.schemas.oauth_schemas import OAuthProviderType, OAuthToken, OAuthUserInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TestOAuthToken:
    def test_create_oauth_token_with_minimal_args(self):
        """最小限の引数でOAuthTokenを作成できることを確認するテスト"""
        token = OAuthToken.create(access_token='test_access_token')

        assert token.access_token == 'test_access_token'
        assert token.refresh_token is None
        assert token.token_type == 'Bearer'
        assert token.expires_at is None
        assert token.scope is None

    def test_create_oauth_token_with_all_args(self, fixed_time):
        """すべての引数でOAuthTokenを作成できることを確認するテスト"""
        token = OAuthToken.create(
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_type='Custom',
            expires_in=3600,
            scope='read write',
        )

        expected_expires_at = fixed_time + timedelta(seconds=3600)

        assert token.access_token == 'test_access_token'
        assert token.refresh_token == 'test_refresh_token'
        assert token.token_type == 'Custom'
        logger.info(f'token.expires_at: {token.expires_at}')
        logger.info(f'expected_expires_at: {expected_expires_at}')
        assert token.expires_at.replace(tzinfo=None) == expected_expires_at
        assert token.scope == 'read write'

    def test_token_immutability(self):
        """OAuthTokenがイミュータブルであることを確認するテスト"""
        token = OAuthToken(access_token='test_access_token')

        with pytest.raises(ValidationError):
            token.access_token = 'new_access_token'

    def test_is_expired_with_no_expiration(self):
        """有効期限がない場合にis_expiredがFalseを返すことを確認するテスト"""
        token = OAuthToken(access_token='test_access_token')

        assert token.is_expired() is False

    def test_is_expired_with_future_expiration(self):
        """有効期限が未来の場合にis_expiredがFalseを返すことを確認するテスト"""
        now = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        future = now + timedelta(hours=1)

        token = OAuthToken(access_token='test_access_token', expires_at=future)

        assert token.is_expired() is False

    def test_is_expired_with_past_expiration(self):
        """有効期限が過去の場合にis_expiredがTrueを返すことを確認するテスト"""
        now = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        past = now - timedelta(hours=1)

        token = OAuthToken(access_token='test_access_token', expires_at=past)

        assert token.is_expired() is True

    def test_is_expired_with_reference_time(self):
        """参照時刻を指定した場合のis_expiredの動作を確認するテスト"""
        reference_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=ZoneInfo('Asia/Tokyo'))

        # 参照時刻より前の有効期限
        past_expires = datetime(2023, 1, 1, 11, 0, 0, tzinfo=ZoneInfo('Asia/Tokyo'))
        token_past = OAuthToken(access_token='test_access_token', expires_at=past_expires)
        assert token_past.is_expired(reference_time) is True

        # 参照時刻より後の有効期限
        future_expires = datetime(2023, 1, 1, 13, 0, 0, tzinfo=ZoneInfo('Asia/Tokyo'))
        token_future = OAuthToken(access_token='test_access_token', expires_at=future_expires)
        assert token_future.is_expired(reference_time) is False


class TestOAuthUserInfo:
    def test_create_oauth_user_info_with_minimal_args(self):
        """最小限の引数でOAuthUserInfoを作成できることを確認するテスト"""
        user_info = OAuthUserInfo(provider=OAuthProviderType.GOOGLE, provider_user_id='12345')

        assert user_info.provider == OAuthProviderType.GOOGLE
        assert user_info.provider_user_id == '12345'
        assert user_info.email is None
        assert user_info.name is None
        assert user_info.picture is None

    def test_create_oauth_user_info_with_all_args(self):
        """すべての引数でOAuthUserInfoを作成できることを確認するテスト"""
        user_info = OAuthUserInfo(
            provider=OAuthProviderType.GITHUB,
            provider_user_id='67890',
            email='test@example.com',
            name='Test User',
            picture='https://example.com/avatar.jpg',
        )

        assert user_info.provider == OAuthProviderType.GITHUB
        assert user_info.provider_user_id == '67890'
        assert user_info.email == 'test@example.com'
        assert user_info.name == 'Test User'
        assert user_info.picture == 'https://example.com/avatar.jpg'

    def test_user_info_immutability(self):
        """OAuthUserInfoがイミュータブルであることを確認するテスト"""
        user_info = OAuthUserInfo(provider=OAuthProviderType.GOOGLE, provider_user_id='12345')

        with pytest.raises(ValidationError):
            user_info.email = 'new@example.com'
