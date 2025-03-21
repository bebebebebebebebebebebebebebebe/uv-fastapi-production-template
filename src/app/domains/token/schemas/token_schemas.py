from datetime import datetime

from pydantic import BaseModel


class BaseJWTPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime


class AccessTokenJWTPayload(BaseJWTPayload):
    email: str | None = None
    role: str = 'user'


class RefreshTokenJWTPayload(BaseJWTPayload):
    pass


class EmailVerificationJWTPayload(BaseJWTPayload):
    email: str
