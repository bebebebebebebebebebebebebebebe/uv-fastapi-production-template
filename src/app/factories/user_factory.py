from abc import ABC, abstractmethod

from src.app.domains.token.services.token_service import TokenService
from src.app.domains.users.services.password_service import BcryptPasswordService, PasswordService
from src.app.infrastructures.users.repositories.user_repository_impl import UserRepositoryImpl
from src.app.usecases.users.user_registration_service import UserRegistrationService


class IUserFactory(ABC):
    @staticmethod
    @abstractmethod
    def create_user_registration_service(
        token_service: TokenService, db_session: any, password_service: PasswordService | None = None
    ) -> UserRegistrationService:
        """
        ユーザー登録サービスを作成します。
        Args:
            token_service (TokenService): トークンサービス。
            db_session (any): データベースセッション。
            password_service (PasswordService | None, optional): パスワードサービス。デフォルトはNone。
        """
        pass


class UserFactory(IUserFactory):
    @staticmethod
    def create_user_registration_service(
        token_service: TokenService, db_session: any, password_service: PasswordService | None = None
    ) -> UserRegistrationService:
        """
        ユーザー登録サービスを作成します。
        Args:
            token_service (TokenService): トークンサービス。
            db_session (any): データベースセッション。
            password_service (PasswordService | None, optional): パスワードサービス。デフォルトはNone。
        """
        if password_service is None:
            password_service = BcryptPasswordService()

        user_repository = UserRepositoryImpl(db_session)
        return UserRegistrationService(token_service, user_repository, password_service)
