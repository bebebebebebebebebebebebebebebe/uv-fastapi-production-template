from datetime import datetime

from pydantic import BaseModel


class SocialAccountBase(BaseModel):
    provider: str
    provider_user_id: str
    provider_email: str


class CreateSocialAccount(SocialAccountBase):
    """ソーシャルアカウント作成用スキーマ (外部APIから使用)"""

    user_id: int
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: datetime | None = None


class CreateInternalSocialAccount(SocialAccountBase):
    """ソーシャルアカウント作成用スキーマ (内部処理用)"""

    user_id: int
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: datetime | None = None


class UpdateSocialAccount(BaseModel):
    provider: str | None = None
    provider_user_id: str | None = None
    provider_email: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: datetime | None = None


class ReadSocialAccount(SocialAccountBase):
    id: int
    user_id: int
    token_expiry: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
