from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.crud.social_account_crud import SocialAccountCRUD
from src.app.crud.user_crud import UserCRUD
from src.app.models.social_account import SocialAccount
from src.app.schemas.social_account_schema import CreateInternalSocialAccount
from src.app.schemas.user_schemas import CreateInternalUser


@pytest.fixture
def social_account_data():
    """テスト用のソーシャルアカウントデータを生成するフィクスチャ"""
    faker = Faker()
    return {
        'provider': 'google',
        'provider_user_id': faker.uuid4(),
        'provider_email': faker.email(),
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'token_expiry': datetime.now(tz=ZoneInfo('Asia/Tokyo')) + timedelta(hours=1),
    }


@pytest_asyncio.fixture
async def local_create_user(get_test_db_async: AsyncSession):
    """テスト用のユーザーを作成するフィクスチャ"""
    faker = Faker()
    username = f'testuser_{faker.uuid4()}'
    email = f'{username}@example.com'

    # 既存ユーザーをクリーンアップ（テスト間での衝突を防ぐため）
    user_crud = UserCRUD(get_test_db_async)

    # 新しいユーザーを作成
    user_data = CreateInternalUser(name='Test User', username=username, email=email, hashed_password='hashedpassword')
    user = await user_crud.create_async(user_data)
    return user


@pytest_asyncio.fixture
async def create_social_account(get_test_db_async: AsyncSession, local_create_user, social_account_data):
    """テスト用のソーシャルアカウントを作成するフィクスチャ"""
    social_account_crud = SocialAccountCRUD(get_test_db_async)
    social_account_data['user_id'] = local_create_user.id
    social_account = await social_account_crud.create_async(CreateInternalSocialAccount(**social_account_data))
    return social_account


@pytest_asyncio.fixture
async def create_multiple_social_accounts(get_test_db_async: AsyncSession, local_create_user, social_account_data):
    """複数のソーシャルアカウントを作成するフィクスチャ"""
    social_account_crud = SocialAccountCRUD(get_test_db_async)

    # google アカウント
    google_account_data = social_account_data.copy()
    google_account_data['provider'] = 'google'
    google_account_data['user_id'] = local_create_user.id
    in_google_data = CreateInternalSocialAccount(**google_account_data)
    google_account = await social_account_crud.create_async(in_google_data)

    # GitHub アカウント
    github_account_data = social_account_data.copy()
    github_account_data['provider'] = 'github'
    github_account_data['user_id'] = local_create_user.id
    github_account_data['provider_user_id'] = 'github_user_id'
    google_account_data['provider_email'] = 'github_email@example.com'
    in_github_data = CreateInternalSocialAccount(**github_account_data)
    github_account = await social_account_crud.create_async(in_github_data)
    return google_account, github_account


class TestSocialAccountCRUD:
    """SocialAccountCRUDのテスト"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, get_test_db_async: AsyncSession):
        """テストの前後処理"""
        self.db = get_test_db_async
        self.social_account_crud = SocialAccountCRUD(self.db)
        await self.db.rollback()
        yield
        # テスト後のクリーンアップ
        try:
            await self.db.execute(SocialAccount.__table__.delete())
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    @pytest.mark.asyncio
    async def test_create_social_account(self, local_create_user, social_account_data):
        """SocialAccountを作成できることを確認するテスト"""
        social_account_data['user_id'] = local_create_user.id
        social_account = await self.social_account_crud.create_async(CreateInternalSocialAccount(**social_account_data))
        assert social_account.provider == social_account_data['provider']
        assert social_account.provider_user_id == social_account_data['provider_user_id']
        assert social_account.provider_email == social_account_data['provider_email']
        assert social_account.token_expiry == social_account_data['token_expiry']
        assert social_account.user_id == local_create_user.id

        # データベースから取得して確認
        db_obj = await self.db.execute(select(SocialAccount).filter_by(id=social_account.id))
        db_obj = db_obj.scalar_one()
        assert db_obj is not None
        assert db_obj.access_token == social_account_data['access_token']
        assert db_obj.refresh_token == social_account_data['refresh_token']
        assert db_obj.provider == social_account_data['provider']
        assert db_obj.provider_user_id == social_account_data['provider_user_id']

    @pytest.mark.asyncio
    async def test_get_by_provider_and_id(self, create_social_account):
        """指定されたプロバイダーとプロバイダーユーザーIDでSocialAccountを取得できることを確認するテスト"""
        result = await self.social_account_crud.get_by_provider_and_id(
            create_social_account.provider, create_social_account.provider_user_id
        )
        assert result is not None
        assert result.id == create_social_account.id
        assert result.provider == create_social_account.provider
        assert result.provider_user_id == create_social_account.provider_user_id

        # 存在しないプロバイダーとIDの組み合わせ
        result = await self.social_account_crud.get_by_provider_and_id('invalid_provider', 'invalid_id')
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, create_multiple_social_accounts, local_create_user):
        """ユーザーIDによるソーシャルアカウント一覧取得のテスト"""
        result = await self.social_account_crud.get_by_user_id(local_create_user.id)
        assert len(result) == 2

        providers = [social_account.provider for social_account in result]
        assert 'google' in providers
        assert 'github' in providers

        # 存在しないユーザーID
        non_existent = await self.social_account_crud.get_by_user_id(9999)
        assert len(non_existent) == 0

    @pytest.mark.asyncio
    async def test_update_tokens(self, create_social_account):
        """トークン更新のテスト"""
        new_access_token = 'new_access_token'
        new_refresh_token = 'new_refresh_token'
        new_token_expiry = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + timedelta(days=1)

        result = await self.social_account_crud.update_tokens(
            create_social_account.id, new_access_token, new_refresh_token, new_token_expiry
        )
        assert result is not None
        assert result.token_expiry == new_token_expiry

        # DBの値も更新されていることを確認
        query = select(SocialAccount).where(SocialAccount.id == create_social_account.id)
        db_result = await self.db.execute(query)
        db_account = db_result.scalar_one()
        assert db_account is not None
        assert db_account.access_token == new_access_token
        assert db_account.refresh_token == new_refresh_token

        # 存在しないIDでの更新
        non_exsistent = await self.social_account_crud.update_tokens(
            9999,
            new_access_token,
            new_refresh_token,
            new_token_expiry,
        )
        assert non_exsistent is None

    @pytest.mark.asyncio
    async def test_delete_by_user_id_and_provider(self, create_social_account, local_create_user):
        """ユーザーIDとプロバイダーによる削除のテスト"""
        result = await self.social_account_crud.delete_by_user_id_and_provider(
            local_create_user.id,
            create_social_account.provider,
        )
        assert result is True

        # 削除されていることを確認
        db_result = await self.db.execute(select(SocialAccount).where(SocialAccount.id == create_social_account.id))
        db_account = db_result.scalar_one_or_none()
        assert db_account is None

        # 存在しないユーザーIDとプロバイダーの組み合わせ
        non_existent = await self.social_account_crud.delete_by_user_id_and_provider(
            9999,
            create_social_account.provider,
        )
        assert non_existent is False

    @pytest.mark.asyncio
    async def test_read_async(self, create_social_account):
        """IDによるソーシャルアカウント取得のテスト"""
        result = await self.social_account_crud.read_async(create_social_account.id)
        assert result is not None
        assert result.id == create_social_account.id
        assert result.provider == create_social_account.provider
        assert result.provider_user_id == create_social_account.provider_user_id

        # 存在しないID
        non_existent = await self.social_account_crud.read_async(9999)
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_read_all_async(self, create_multiple_social_accounts):
        """全ソーシャルアカウント取得のテスト"""
        result = await self.social_account_crud.read_all_async()
        assert result is not None
        assert len(result) == 2

        # プロバイダーでフィルタリング
        google_accounts = await self.social_account_crud.read_all_async({'provider': 'google'})
        assert len(google_accounts) == 1
        assert google_accounts[0].provider == 'google'

        github_accounts = await self.social_account_crud.read_all_async({'provider': 'github'})
        assert len(github_accounts) == 1
        assert github_accounts[0].provider == 'github'

        # 存在しないプロバイダー
        invalid_provider = await self.social_account_crud.read_all_async({'provider': 'invalid_provider'})
        assert len(invalid_provider) == 0
