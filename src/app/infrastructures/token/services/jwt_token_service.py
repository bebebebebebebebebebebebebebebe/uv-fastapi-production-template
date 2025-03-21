from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jose import jwt

from src.app.core.config import settings
from src.app.domains.token.schemas.token_schemas import AccessTokenJWTPayload, EmailVerificationJWTPayload, RefreshTokenJWTPayload
from src.app.domains.token.services.token_service import InvalidTokenException, TokenService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JWTTokenService(TokenService):
    """
    JWT（JSON Web Token）を使用したトークンサービスの実装。
    """

    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        """
        JWTトークンサービスの初期化。
        Args:
            secret_key (str): シークレットキー。
            algorithm (str): トークンの暗号化アルゴリズム。デフォルトは 'HS256'。
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        user_id: str,
        email: str | None = None,
        role: str = 'user',
        expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    ) -> str:
        """
        Accessトークンを作成する。

        Args:
            user_id (str): ユーザーID。
            email (str, optional): メールアドレス。デフォルトはNone。
            role (str, optional): ロール。デフォルトは 'user'。
            expires_delta (timedelta, optional): トークンの有効期限。デフォルトは settings.ACCESS_TOKEN_EXPIRE_MINUTES 分。
        Returns:
            str: 作成されたAccessトークン。
        """
        expire = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + expires_delta
        payload = AccessTokenJWTPayload(
            sub=user_id,
            email=email,
            role=role,
            exp=expire,
            iat=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
        )
        logger.info(f'encoded iat: {payload.iat}')  # 2023-01-01 09:00:00
        encoded_jwt = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
        decode_jwt = jwt.decode(encoded_jwt, self.secret_key, algorithms=[self.algorithm])
        logger.info(f'decoded iat: {datetime.fromtimestamp(decode_jwt["iat"])}')  # 2023-01-01 00:00:00
        return encoded_jwt

    def create_refresh_token(self, user_id: str, expires_delta: timedelta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)) -> str:
        expire = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + expires_delta
        payload = RefreshTokenJWTPayload(
            sub=user_id,
            exp=expire,
            iat=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
        )
        encoded_jwt = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_email_verification_token(
        self,
        user_id: str,
        email: str | None = None,
        expires_delta: timedelta = timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES),
    ) -> str:
        expire = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + expires_delta
        payload = EmailVerificationJWTPayload(
            sub=user_id,
            email=email,
            exp=expire,
            iat=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
        )
        encoded_jwt = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.JWTError:
            raise InvalidTokenException('Invalid token')
