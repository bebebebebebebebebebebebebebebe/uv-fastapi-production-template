from src.app.domains.users.repositories.user_repository import UserRepositoryInterface
from src.app.domains.users.schemas.user_schemas import Email


class UserService:
    """
    ユーザー関連のビジネスロジックを提供するサービスクラス。
    ユーザーのメールアドレスの一意性を確認するなどの機能を提供します。
    """

    def __init__(self, user_repository: UserRepositoryInterface):
        self.user_repository = user_repository

    async def is_email_unique(self, email: Email) -> bool:
        """
        メールアドレスが既存のユーザーと重複していないかを確認します。
        Args:
            email (Email): 確認するメールアドレス
        Returns:
                bool: メールアドレスが重複していない場合はTrue、重複している場合はFalse
        """
        return not await self.user_repository.email_exists(email)

    async def is_username_unique(self, username: str) -> bool:
        """
        ユーザー名が既存のユーザーと重複していないかを確認します。
        Args:
            username (str): 確認するユーザー名
        Returns:
                bool: ユーザー名が重複していない場合はTrue、重複している場合はFalse
        """
        return not await self.user_repository.username_exists(username)
