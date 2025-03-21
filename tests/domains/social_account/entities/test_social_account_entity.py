from datetime import datetime, timedelta

import pytest
from src.app.domains.social_accounts.entities.social_account_entity import SocialAccountEntity
from src.app.domains.social_accounts.schemas.social_account_schemas import ProviderEmail


@pytest.fixture
def provider_email():
    return ProviderEmail(email='test@example.com')


@pytest.fixture
def social_account(provider_email: ProviderEmail, fixed_time: datetime) -> SocialAccountEntity:
    return SocialAccountEntity(
        provider='google',
        provider_user_id='12345',
        provider_email=provider_email,
        access_token='initial_access_token',
        refresh_token='initial_refresh_token',
        created_at=fixed_time,
    )


class TestSocialAccountEntity:
    def test_initialization(self, social_account: SocialAccountEntity, provider_email: ProviderEmail, fixed_time: datetime):
        """ソーシャルアカウントエンティティが正しく初期化されるかテスト"""
        assert social_account.provider == 'google'
        assert social_account.provider_user_id == '12345'
        assert social_account.provider_email == provider_email
        assert social_account.access_token == 'initial_access_token'
        assert social_account.refresh_token == 'initial_refresh_token'
        assert social_account.created_at == fixed_time
        assert social_account.id is None
        assert social_account.user_id is None
        assert social_account.token_expiry is None
        assert social_account.provider_profile_image_url is None
        assert social_account.updated_at is None

    def test_update_tokens(self, social_account: SocialAccountEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime):
        """トークン更新メソッドが正しく動作するかテスト"""
        update_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: update_time)

        new_access_token = 'new_access_token'
        new_refresh_token = 'new_refresh_token'
        expires_at = fixed_time + timedelta(days=7)

        social_account.update_tokens(
            new_access_token,
            new_refresh_token,
            expires_at,
        )

        # 更新されたことを検証
        assert social_account.access_token == new_access_token
        assert social_account.refresh_token == new_refresh_token
        assert social_account.token_expiry == expires_at
        assert social_account.updated_at == update_time

    def test_update_tokens_with_partial_data(
        self, social_account: SocialAccountEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime
    ):
        """部分的なデータでトークン更新が正しく動作するかテスト"""
        update_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: update_time)

        new_access_token = 'new_access_token'
        social_account.update_tokens(access_token=new_access_token)
        assert social_account.access_token == new_access_token
        assert social_account.refresh_token is None
        assert social_account.token_expiry is None
        assert social_account.updated_at == update_time

    def test_repr(self, social_account: SocialAccountEntity):
        """__repr__メソッドが正しくエンティティを表現しているかテスト"""
        repr_str = repr(social_account)
        assert 'SocialAccountEntity' in repr_str
        assert 'provider=google' in repr_str
        assert 'provider_user_id=12345' in repr_str
