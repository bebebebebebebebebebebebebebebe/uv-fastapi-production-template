from src.app.core.dto.entity_with_model_dto import EntityWithModelDTO
from src.app.core.schemas.global_value_objects import EntityUUID
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.schemas.user_schemas import Email, FullName
from src.app.models.user import User
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserEntityDTO(EntityWithModelDTO[UserEntity, User]):
    """
    UserエンティティとUserモデル間の変換を担当するDTOクラス
    """

    @staticmethod
    def to_entity(model: User) -> UserEntity:
        """
        UserモデルからUserEntityを作成します。
        Args:
            model (User): Userモデル
        Returns:
            UserEntity: UserEntityインスタンス
        """
        full_name = None
        if model.full_name:
            parts = model.full_name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
            full_name = FullName(first_name=first_name, last_name=last_name)

        return UserEntity(
            id=model.id,
            username=model.username,
            email=Email(email=model.email),
            full_name=full_name,
            hashed_password=model.hashed_password,
            is_verified=model.is_verified,
            uuid=EntityUUID(value=model.uuid),
            profile_image_url=model.profile_image_url,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            is_deleted=model.is_deleted,
        )

    @staticmethod
    def to_model(entity: UserEntity) -> User:
        """
        UserEntityからUserモデルを作成するためのデータ辞書を作成します。
        Args:
            entity (UserEntity): UserEntityインスタンス
        Returns:
            dict: Userモデル
        """
        data = {
            'id': entity.id,
            'username': entity.username,
            'email': entity.email.email,
            'is_verified': entity.is_verified,
            'uuid': str(entity.uuid.value),
            'created_at': entity.created_at,
        }

        # 任意フィールド
        if entity.full_name:
            data['full_name'] = str(entity.full_name)

        if entity.hashed_password:
            data['hashed_password'] = entity.hashed_password

        if entity.profile_image_url:
            data['profile_image_url'] = entity.profile_image_url

        return User(**data)
