import uuid
from datetime import timedelta

import pytest
from src.app.core.schemas.global_value_objects import EntityUUID
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.schemas.user_schemas import Email, FullName
from src.app.infrastructures.users.dtos.user_dto import UserEntityDTO
from src.app.models.user import User
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TestUserEntityDTO:
    @pytest.fixture
    def entity_uuid(self):
        """テスト用のEntityUUID"""
        return EntityUUID(value=uuid.UUID('12345678-1234-5678-1234-567812345678'))

    @pytest.fixture
    def user_model_with_full_name(self, random_password, fixed_time):
        """フルネームを持つUserモデルのフィクスチャ"""
        user = User(
            id=1,
            username='testuser',
            email='test@example.com',
            full_name='John Doe',
            hashed_password=random_password,
            is_verified=True,
            uuid=uuid.UUID('12345678-1234-5678-1234-567812345678'),
            profile_image_url='https://example.com/profile.jpg',
            created_at=fixed_time,
            updated_at=fixed_time + timedelta(hours=1),
            deleted_at=None,
            is_deleted=False,
        )
        # social_accountsはリレーションシップなので、空リストを設定
        user.social_accounts = []
        return user

    @pytest.fixture
    def user_model_without_full_name(self, random_password, fixed_time):
        """フルネームを持たないUserモデルのフィクスチャ"""
        user = User(
            id=2,
            username='testuser2',
            email='test2@example.com',
            full_name=None,
            hashed_password=random_password,
            is_verified=False,
            uuid=uuid.UUID('12345678-1234-5678-1234-567812345678'),
            profile_image_url=None,
            created_at=fixed_time,
            updated_at=None,
            deleted_at=None,
            is_deleted=False,
        )
        user.social_accounts = []
        return user

    @pytest.fixture
    def user_entity_with_full_name(self, random_password, fixed_time, entity_uuid):
        """フルネームを持つUserEntityのフィクスチャ"""
        return UserEntity(
            id=1,
            username='testuser',
            email=Email(email='test@example.com'),
            full_name=FullName(first_name='John', last_name='Doe'),
            hashed_password=random_password,
            is_verified=True,
            uuid=entity_uuid,
            profile_image_url='https://example.com/profile.jpg',
            created_at=fixed_time,
            updated_at=fixed_time + timedelta(hours=1),
            deleted_at=None,
            is_deleted=False,
        )

    @pytest.fixture
    def user_entity_without_full_name(self, random_password, fixed_time, entity_uuid):
        """フルネームを持たないUserEntityのフィクスチャ"""
        return UserEntity(
            id=2,
            username='testuser2',
            email=Email(email='test2@example.com'),
            full_name=None,
            hashed_password=random_password,
            is_verified=False,
            uuid=entity_uuid,
            profile_image_url=None,
            created_at=fixed_time,
            updated_at=None,
            deleted_at=None,
            is_deleted=False,
        )

    def test_to_entity_with_full_name(self, user_model_with_full_name):
        """フルネームを持つモデルからエンティティへの変換をテスト"""
        # テスト実行
        entity = UserEntityDTO.to_entity(user_model_with_full_name)

        # 検証
        assert isinstance(entity, UserEntity)
        assert entity.id == 1
        assert entity.username == 'testuser'
        assert entity.email.email == 'test@example.com'
        assert entity.full_name is not None
        assert entity.full_name.first_name == 'John'
        assert entity.full_name.last_name == 'Doe'
        assert str(entity.full_name) == 'John Doe'
        assert entity.hashed_password == user_model_with_full_name.hashed_password
        assert entity.is_verified is True
        assert str(entity.uuid.value) == '12345678-1234-5678-1234-567812345678'
        assert entity.profile_image_url == 'https://example.com/profile.jpg'
        assert entity.is_deleted is False
        assert entity.deleted_at is None

    def test_to_entity_without_full_name(self, user_model_without_full_name):
        """フルネームを持たないモデルからエンティティへの変換をテスト"""
        # テスト実行
        entity = UserEntityDTO.to_entity(user_model_without_full_name)

        # 検証
        assert isinstance(entity, UserEntity)
        assert entity.id == 2
        assert entity.username == 'testuser2'
        assert entity.email.email == 'test2@example.com'
        assert entity.full_name is None
        assert entity.hashed_password == user_model_without_full_name.hashed_password
        assert entity.is_verified is False
        assert str(entity.uuid.value) == '12345678-1234-5678-1234-567812345678'
        assert entity.profile_image_url is None
        assert entity.is_deleted is False
        assert entity.deleted_at is None

    def test_to_model_with_full_name(self, user_entity_with_full_name):
        """フルネームを持つエンティティからモデルへの変換をテスト"""
        # テスト実行
        model = UserEntityDTO.to_model(user_entity_with_full_name)

        # 検証
        assert isinstance(model, User)
        assert model.username == 'testuser'
        assert model.email == 'test@example.com'
        assert model.full_name == 'John Doe'
        assert model.hashed_password == user_entity_with_full_name.hashed_password
        assert model.is_verified is True
        assert str(model.uuid) == '12345678-1234-5678-1234-567812345678'
        assert model.profile_image_url == 'https://example.com/profile.jpg'
        assert model.is_deleted is False
        assert model.deleted_at is None

    def test_to_model_without_full_name(self, user_entity_without_full_name):
        """フルネームを持たないエンティティからモデルへの変換をテスト"""
        # テスト実行
        model = UserEntityDTO.to_model(user_entity_without_full_name)

        # 検証
        assert isinstance(model, User)
        assert model.username == 'testuser2'
        assert model.email == 'test2@example.com'
        assert model.full_name is None
        assert model.hashed_password == user_entity_without_full_name.hashed_password
        assert model.is_verified is False
        assert str(model.uuid) == '12345678-1234-5678-1234-567812345678'
        assert model.profile_image_url is None
        assert model.is_deleted is False
        assert model.deleted_at is None

    def test_to_entity_with_complex_full_name(self):
        """複合姓名を持つケースのテスト"""
        # 3つ以上の単語を含むフルネームのテスト
        user = User(
            id=3,
            username='testuser3',
            email='test3@example.com',
            full_name='John van der Doe',
            is_verified=True,
            uuid=uuid.UUID('12345678-1234-5678-1234-567812345678'),
        )
        user.social_accounts = []

        # テスト実行
        entity = UserEntityDTO.to_entity(user)

        # 検証
        assert entity.full_name is not None
        assert entity.full_name.first_name == 'John'
        # 名前の最初の部分以外はすべて姓として扱われる
        assert entity.full_name.last_name == 'van der Doe'

    def test_roundtrip_conversion(self, user_entity_with_full_name):
        """エンティティ→モデル→エンティティの往復変換をテスト"""
        # エンティティからモデルへ
        model = UserEntityDTO.to_model(user_entity_with_full_name)
        # モデルからエンティティへ
        entity = UserEntityDTO.to_entity(model)

        # 元のエンティティと同じ値を持つことを検証
        assert entity.id == user_entity_with_full_name.id
        assert entity.username == user_entity_with_full_name.username
        assert entity.email.email == user_entity_with_full_name.email.email
        assert str(entity.full_name) == str(user_entity_with_full_name.full_name)
        assert entity.is_verified == user_entity_with_full_name.is_verified
        assert str(entity.uuid.value) == str(user_entity_with_full_name.uuid.value)
        assert entity.profile_image_url == user_entity_with_full_name.profile_image_url
