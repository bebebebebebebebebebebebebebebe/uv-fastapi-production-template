from datetime import datetime, timedelta

import pytest
from src.app.core.schemas.global_value_objects import EntityUUID
from src.app.domains.social_accounts.entities.social_account_entity import SocialAccountEntity
from src.app.domains.social_accounts.schemas.social_account_schemas import ProviderEmail
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.schemas.user_schemas import Email, FullName
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def user_full_name():
    """ユーザーのFullName値オブジェクト"""
    return FullName(first_name='John', last_name='Doe')


@pytest.fixture
def user_email():
    """ユーザーのEmail値オブジェクト"""
    return Email(email='user@example.com')


@pytest.fixture
def provider_email():
    """ソーシャルアカウント用のProviderEmail値オブジェクト"""
    return ProviderEmail(email='social@example.com')


@pytest.fixture
def mock_entity_uuid(monkeypatch):
    """EntityUUID.generateをモックして固定のUUIDを返すようにする"""
    uuid_value = '123e4567-e89b-12d3-a456-426614174000'
    uuid = EntityUUID(value=uuid_value)
    monkeypatch.setattr(EntityUUID, 'generate', lambda: uuid)
    return uuid


@pytest.fixture
def social_account(provider_email: ProviderEmail, fixed_time: datetime):
    """テスト用のSocialAccountEntityを作成"""
    return SocialAccountEntity(provider='google', provider_user_id='12345', provider_email=provider_email, created_at=fixed_time)


@pytest.fixture
def user_entity(user_full_name, user_email, mock_entity_uuid, fixed_time):
    """テスト用の基本的なUserEntityを作成"""
    return UserEntity(
        full_name=user_full_name,
        username='testuser',
        email=user_email,
        created_at=fixed_time,
        uuid=mock_entity_uuid,
    )


class TestUserEntity:
    """UserEntityクラスのテスト"""

    def test_initialization(
        self, user_entity: UserEntity, user_full_name: FullName, user_email: Email, mock_entity_uuid: EntityUUID, fixed_time: datetime
    ):
        """UserEntityが初期値で正しく初期化されるかテスト"""
        assert user_entity.full_name == user_full_name
        assert user_entity.full_name.first_name == 'John'
        assert user_entity.full_name.last_name == 'Doe'
        assert str(user_entity.full_name) == 'John Doe'
        assert user_entity.username == 'testuser'
        assert user_entity.email == user_email
        assert user_entity.is_verified is False
        assert user_entity.uuid == mock_entity_uuid
        assert user_entity.created_at == fixed_time
        assert user_entity.updated_at is None
        assert user_entity.deleted_at is None
        assert user_entity.is_deleted is False
        assert user_entity.social_accounts == []

    def test_mark_as_verified(self, user_entity: UserEntity, fixed_time: datetime, monkeypatch: pytest.MonkeyPatch):
        """ユーザーを認証済みとしてマークするテスト"""
        verification_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: verification_time)
        user_entity.mark_as_verified()
        assert user_entity.is_verified is True
        assert user_entity.updated_at == verification_time

    def test_update_profile_all_fields(self, user_entity: UserEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime):
        """全てのプロフィールフィールドを更新するテスト"""
        new_full_name = FullName(first_name='Jane', last_name='Doe')
        new_username = 'newuser'
        new_profile_image_url = 'https://example.com/new_profile_image.jpg'
        updated_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: updated_time)
        user_entity.update_profile(full_name=new_full_name, username=new_username, profile_image_url=new_profile_image_url)
        assert user_entity.full_name == new_full_name
        assert user_entity.username == new_username
        assert user_entity.profile_image_url == new_profile_image_url
        assert user_entity.updated_at == updated_time

    def test_update_profile_partial(self, user_entity: UserEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime):
        """一部のプロフィールフィールドのみを更新するテスト"""
        update_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: update_time)
        user_entity.update_profile(full_name=FullName(first_name='Jane', last_name='Doe'))
        assert user_entity.full_name.first_name == 'Jane'
        assert user_entity.full_name.last_name == 'Doe'
        assert user_entity.username == 'testuser'
        assert user_entity.profile_image_url is None
        assert user_entity.updated_at == update_time

    def test_set_password(self, user_entity: UserEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime, random_password: str):
        """パスワードハッシュを設定するテスト"""
        hashed_password = random_password
        update_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: update_time)
        user_entity.set_password(hashed_password)
        assert user_entity.hashed_password == hashed_password
        assert user_entity.updated_at == update_time

    def test_add_social_account(self, user_entity, social_account, monkeypatch, fixed_time):
        """ソーシャルアカウントを追加するテスト"""
        update_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: update_time)
        user_entity.add_social_account(social_account)

        assert len(user_entity.social_accounts) == 1
        assert user_entity.social_accounts[0] == social_account
        assert user_entity.updated_at == update_time

    def test_remove_social_account(
        self, user_entity: UserEntity, social_account: SocialAccountEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime
    ):
        """ソーシャルアカウントを削除するテスト"""
        user_entity.add_social_account(social_account)
        assert len(user_entity.social_accounts) == 1

        updated_time = fixed_time + timedelta(hours=2)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: updated_time)

        user_entity.remove_social_account(provider=social_account.provider, provider_user_id=social_account.provider_user_id)
        assert len(user_entity.social_accounts) == 0
        assert user_entity.updated_at == updated_time

    def test_remove_nonexistent_social_account(self, user_entity, monkeypatch, fixed_time):
        """存在しないソーシャルアカウントを削除する場合のテスト"""
        update_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: update_time)

        user_entity.remove_social_account(provider='nonexistent', provider_user_id='nonexistent')
        assert len(user_entity.social_accounts) == 0
        assert user_entity.updated_at == update_time

    def test_mark_as_deleted(self, user_entity: UserEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime):
        """ユーザーを論理削除としてマークするテスト"""
        deletion_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: deletion_time)

        user_entity.mark_as_deleted()
        assert user_entity.is_deleted is True
        assert user_entity.deleted_at == deletion_time
        assert user_entity.updated_at == deletion_time

    def test_mark_as_deleted_already_deleted(self, user_entity, monkeypatch, fixed_time):
        """すでに削除済みのユーザーを再度削除としてマークするテスト"""
        deletion_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: deletion_time)
        user_entity.mark_as_deleted()

        new_time = fixed_time + timedelta(hours=2)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: new_time)
        user_entity.mark_as_deleted()

        # deleted_atは最初の削除時間のままであるべき
        assert user_entity.deleted_at == deletion_time
        assert user_entity.updated_at == new_time

    def test_restore_deleted_user(self, user_entity: UserEntity, monkeypatch: pytest.MonkeyPatch, fixed_time: datetime):
        """削除されたユーザーを復元するテスト"""
        deletion_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: deletion_time)
        user_entity.mark_as_deleted()
        assert user_entity.is_deleted is True

        restore_time = fixed_time + timedelta(hours=2)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: restore_time)
        user_entity.restore()

        assert user_entity.is_deleted is False
        assert user_entity.deleted_at is None
        assert user_entity.updated_at == restore_time

    def test_restore_non_deleted_user(self, user_entity, monkeypatch, fixed_time):
        """削除されていないユーザーを復元しても何も変更されないことをテスト"""
        restore_time = fixed_time + timedelta(hours=1)
        monkeypatch.setattr(datetime, 'now', lambda tz=None: restore_time)

        user_entity.restore()
        assert user_entity.is_deleted is False
        assert user_entity.deleted_at is None
        assert user_entity.updated_at is None

    def test_repr(self, user_entity):
        """__repr__メソッドのテスト"""
        repr_str = repr(user_entity)
        assert 'UserEntity' in repr_str
        assert f'full_name={user_entity.full_name}' in repr_str
        assert 'username=testuser' in repr_str
        assert f'email={user_entity.email}' in repr_str
