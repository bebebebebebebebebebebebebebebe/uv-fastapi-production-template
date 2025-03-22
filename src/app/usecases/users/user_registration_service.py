from src.app.domains.token.services.token_service import TokenService
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.repositories.user_repository import UserRepositoryInterface
from src.app.domains.users.schemas.user_schemas import Email, FullName, Password
from src.app.domains.users.services.password_service import PasswordService
from src.app.domains.users.services.user_service import UserService
from src.app.usecases.users.dtos.user_dto import UserRegistrationRequest, UserResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmailAlreadyExistsError(Exception):
    """メールアドレスが既に存在する場合に発生する例外"""

    pass


class UsernameAlreadyExistsError(Exception):
    """ユーザー名が既に存在する場合に発生する例外"""

    pass


class UserRegistrationService:
    """
    ユーザー登録のためのサービスクラス。
    """

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordService,
        user_service: UserService,
        token_service: TokenService | None = None,
    ):
        self.user_repository = user_repository
        self.password_service = password_service
        self.user_service = user_service
        self.token_service = token_service

    async def register_user(self, request: UserRegistrationRequest) -> UserResponse:
        """
        ユーザーを登録します。
        Args:
            user_registration_request (UserRegistrationRequest): ユーザー登録のリクエストデータ。
        Returns:
            UserResponse: 登録されたユーザーのレスポンスデータ。
        Raises:
            EmailAlreadyExistsError: メールアドレスが既に存在する場合。
            UsernameAlreadyExistsError: ユーザー名が既に存在する場合。
        """
        email = Email(email=request.email)
        if not self.user_service.is_email_unique(email):
            logger.error(f'メールアドレスが既に存在します: {email}')
            raise EmailAlreadyExistsError(f'メールアドレスが既に存在します: {email}')

        if not self.user_service.is_username_unique(request.username):
            logger.error(f'ユーザー名が既に存在します: {request.username}')
            raise UsernameAlreadyExistsError(f'ユーザー名が既に存在します: {request.username}')

        password = Password(password=request.password)
        hashed_password = self.password_service.hash_password(password)
        full_name = FullName(first_name=request.first_name, last_name=request.last_name)
        user_entity = UserEntity(
            username=request.username,
            email=email,
            full_name=full_name,
            profile_image_url=request.profile_image_url,
        )
        user_entity.set_password(hashed_password)
        create_user = await self.user_repository.create_user(user_entity)
        return UserResponse(
            id=create_user.id,
            uuid=create_user.uuid,
            full_name=str(create_user.full_name) if user_entity.full_name else '',
            username=create_user.username,
            email=create_user.email,
            is_verified=create_user.is_verified,
            profile_image_url=create_user.profile_image_url,
            created_at=create_user.created_at,
            updated_at=create_user.updated_at,
        )
