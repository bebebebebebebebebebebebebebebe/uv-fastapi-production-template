from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.domains.users.dtos.user_dtos import CreateInternalUser, UpdateInternalUser
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.repositories.user_repository import UserRepositoryInterface
from src.app.domains.users.schemas.user_schemas import Email
from src.app.infrastructures.users.dtos.user_entity_dto import UserEntityDTO
from src.app.models.user import User
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepositoryImpl(UserRepositoryInterface):
    """
    UserRepositoryInterfaceの実装クラス。
    SQLAlchemyを使用してデータベースアクセスを行います。
    """

    def __init__(self, db_session: AsyncSession):
        """
        Arguments:
            db_session (AsyncSession): SQLAlchemyのAsyncSessionオブジェクト。
        """
        self.db_session = db_session

    async def create_user(self, create_dto: CreateInternalUser) -> UserEntity:
        """
        ユーザーを作成します。

        Args:
            create_dto (CreateInternalUser): 作成するユーザーの情報を含むDTO。
        returns:
            UserEntity: 作成されたユーザーのエンティティ。
        """
        user_model = User(
            username=create_dto.username,
            email=create_dto.email,
            full_name=create_dto.full_name,
            hashed_password=create_dto.hashed_password,
            is_verified=create_dto.is_verified,
            profile_image_url=create_dto.profile_image_url,
            created_at=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
        )
        self.db_session.add(user_model)
        await self.db_session.commit()
        await self.db_session.refresh(user_model)
        return UserEntityDTO.to_entity(user_model)

    async def find_by_id(self, user_id: int) -> UserEntity | None:
        """
        指定されたIDのユーザーを取得します。
        存在しない場合はNoneを返します。

        Args:
            user_id (int): 取得するユーザーのID。
        returns:
            UserEntity | None: ユーザーのエンティティまたはNone。
        """
        query = select(User).where(User.id == user_id)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        if user_data is None:
            return None

        return UserEntityDTO.to_entity(user_data)

    async def find_by_email(self, email: Email) -> UserEntity | None:
        """
        指定されたメールアドレスのユーザーを取得します。
        存在しない場合はNoneを返します。
        Args:
            email (Email): 取得するユーザーのメールアドレス。
        returns:
            UserEntity | None: ユーザーのエンティティまたはNone。
        """
        query = select(User).where(User.email == email.email)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        if user_data is None:
            return None

        return UserEntityDTO.to_entity(user_data)

    async def find_by_username(self, username: str) -> UserEntity | None:
        """
        指定されたユーザー名のユーザーを取得します。
        存在しない場合はNoneを返します。
        Args:
            username (str): 取得するユーザーのユーザー名。
        returns:
            UserEntity | None:
        """
        query = select(User).where(User.username == username)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        if user_data is None:
            return None

        return UserEntityDTO.to_entity(user_data)

    async def update(self, update_dto: UpdateInternalUser) -> UserEntity:
        """
        ユーザー情報を更新します。
        Args:
            update_dto (UpdateInternalUser): 更新するユーザーの情報を含むDTO。
        returns:
            UserEntity: 更新されたユーザーのエンティティ。
        """
        query = select(User).where(User.id == update_dto.id)
        result = await self.db_session.execute(query)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            raise ValueError(f'User with ID {update_dto.id} not found')

        if update_dto.username is not None:
            user_model.username = update_dto.username

        if update_dto.email is not None:
            user_model.email = update_dto.email

        if update_dto.full_name is not None:
            user_model.full_name = update_dto.full_name

        if update_dto.hashed_password is not None:
            user_model.hashed_password = update_dto.hashed_password

        if update_dto.is_verified is not None:
            user_model.is_verified = update_dto.is_verified

        if update_dto.profile_image_url is not None:
            user_model.profile_image_url = update_dto.profile_image_url

        user_model.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        await self.db_session.commit()
        await self.db_session.refresh(user_model)
        return UserEntityDTO.to_entity(user_model)

    async def delete(self, user_id: int) -> None:
        """
        指定されたIDのユーザーを削除します。
        Args:
            user_id (int): 削除するユーザーのID。
        """
        query = select(User).where(User.id == user_id)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        if user_data is None:
            return  # ユーザーが存在しない場合は何もしない

        await self.db_session.delete(user_data)
        await self.db_session.commit()

    async def logical_delete(self, user_id: int) -> None:
        """
        指定されたIDのユーザーを論理削除します。
        Args:
            user_id (int): 論理削除するユーザーのID。
        """
        query = select(User).where(User.id == user_id)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        if user_data is None:
            return  # ユーザーが存在しない場合は何もしない

        user_data.is_deleted = True
        user_data.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        user_data.deleted_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

        await self.db_session.commit()

    async def email_exists(self, email: Email) -> bool:
        """
        指定されたメールアドレスのユーザーが存在するかどうかを確認します。
        Args:
            email (Email): 確認するメールアドレス。
        returns:
            bool: ユーザーが存在する場合はTrue、存在しない場合はFalse。
        """
        query = select(User).where(User.email == email.email)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        return user_data is not None

    async def username_exists(self, username: str) -> bool:
        """
        指定されたユーザー名のユーザーが存在するかどうかを確認します。
        Args:
            username (str): 確認するユーザー名。
        returns:
            bool: ユーザーが存在する場合はTrue、存在しない場合はFalse。
        """
        query = select(User).where(User.username == username)
        result = await self.db_session.execute(query)
        user_data = result.scalar_one_or_none()

        return user_data is not None
