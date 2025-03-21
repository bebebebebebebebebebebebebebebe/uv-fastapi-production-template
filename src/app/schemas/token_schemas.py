from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TokenType(str, Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'
    EMAIL_VERIFICATION = 'email_verification'


class JWTPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime
    token_type: TokenType


class AccessTokenJWTPayload(JWTPayload):
    email: str
    role: str = 'user'


class RefreshTokenJWTPayload(JWTPayload):
    pass


class EmailVerificationJWTPayload(JWTPayload):
    email: str
    role: str = 'user'


class TokenUserData(BaseModel):
    id: int
    email: str
    role: str = 'user'


class VerifyTokenResponse(BaseModel):
    id: str
    email: str
    role: str = 'user'
    token_type: TokenType
    exp: datetime


class GoogleOAuthPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    iss: str
    aud: str
    azp: str


class GoogleOAuthPayloadWithEmail(GoogleOAuthPayload):
    email: str
    email_verified: bool


class GoogleOAuthPayloadWithProile(GoogleOAuthPayload):
    name: str
    picture: str


class GoogleOAuthUserPayload(GoogleOAuthPayloadWithEmail, GoogleOAuthPayloadWithProile):
    pass
