from abc import ABC, abstractmethod

from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.schemas.user_schemas import Email


class UserRepositoryInterface(ABC):
    @abstractmethod
    async def create_user(self, user: UserEntity) -> UserEntity:
        """
        ユーザーを作成します。

        Args:
            user (UserEntity): 作成するユーザーの情報を含むエンティティ。
        returns:
            UserEntity: 作成されたユーザーのエンティティ。
        """
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> UserEntity | None:
        """
        指定されたIDのユーザーを取得します。
        存在しない場合はNoneを返します。

        Args:
            user_id (int): 取得するユーザーのID。
        returns:
            UserEntity | None: ユーザーのエンティティまたはNone。
        """
        pass

    @abstractmethod
    async def find_by_email(self, email: Email) -> UserEntity | None:
        """
        指定されたメールアドレスのユーザーを取得します。
        存在しない場合はNoneを返します。
        Args:
            email (Email): 取得するユーザーのメールアドレス。
        returns:
            UserEntity | None: ユーザーのエンティティまたはNone。
        """
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> UserEntity | None:
        """
        指定されたユーザー名のユーザーを取得します。
        存在しない場合はNoneを返します。
        Args:
            username (str): 取得するユーザーのユーザー名。
        returns:
            UserEntity | None:
        """
        pass

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        """
        ユーザー情報を更新します。
        Args:
            user (UserEntity): 更新するユーザーのエンティティ。
        returns:
            UserEntity: 更新されたユーザーのエンティティ。
        """
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        """
        指定されたIDのユーザーを削除します。
        Args:
            user_id (int): 削除するユーザーのID。
        """
        pass

    @abstractmethod
    async def logical_delete(self, user_id: int) -> None:
        """
        指定されたIDのユーザーを論理削除します。
        Args:
            user_id (int): 論理削除するユーザーのID。
        """
        pass

    @abstractmethod
    async def email_exists(self, email: Email) -> bool:
        """
        指定されたメールアドレスのユーザーが存在するかどうかを確認します。
        Args:
            email (Email): 確認するメールアドレス。
        returns:
            bool: ユーザーが存在する場合はTrue、存在しない場合はFalse。
        """
        pass

    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """
        指定されたユーザー名のユーザーが存在するかどうかを確認します。
        Args:
            username (str): 確認するユーザー名。
        returns:
            bool: ユーザーが存在する場合はTrue、存在しない場合はFalse。
        """
        pass
