from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jose import JWTError, jwt

from src.app.core.config import settings
from src.app.schemas.token_schemas import (
    AccessTokenJWTPayload,
    EmailVerificationJWTPayload,
    RefreshTokenJWTPayload,
    TokenType,
    TokenUserData,
    VerifyTokenResponse,
)


class JWTTokenService:
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, data: TokenUserData, expires_delta: timedelta = timedelta(minutes=15)) -> str:
        expire = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + expires_delta
        payload = AccessTokenJWTPayload(
            sub=str(data.id),
            email=data.email,
            role=data.role,
            exp=expire,
            iat=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
            token_type=TokenType.ACCESS,
        )
        encoded_jwt = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: TokenUserData, expires_delta: timedelta = timedelta(days=7)) -> str:
        expire = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + expires_delta
        payload = RefreshTokenJWTPayload(
            sub=str(data.id),
            exp=expire,
            iat=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
            token_type=TokenType.REFRESH,
        )
        encoded_jwt = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_email_verification_token(self, data: TokenUserData, expires_delta: timedelta = timedelta(minutes=15)) -> str:
        expire = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + expires_delta
        payload = EmailVerificationJWTPayload(
            sub=str(data.id),
            email=data.email,
            exp=expire,
            iat=datetime.now(tz=ZoneInfo('Asia/Tokyo')),
            token_type=TokenType.EMAIL_VERIFICATION,
        )
        encoded_jwt = jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> VerifyTokenResponse | None:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            return VerifyTokenResponse(
                id=payload.get('sub'),
                email=payload.get('email'),
                role=payload.get('role'),
                exp=payload.get('exp'),
                token_type=payload.get('token_type'),
            )
        except JWTError:
            return None


token_service = JWTTokenService(
    secret_key=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM,
)
