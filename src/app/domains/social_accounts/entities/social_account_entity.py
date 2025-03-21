from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from src.app.domains.social_accounts.schemas.social_account_schemas import ProviderEmail


@dataclass
class SocialAccountEntity:
    """ソーシャルアカウントのエンティティ"""

    provider: str
    provider_user_id: str
    provider_email: ProviderEmail
    id: int | None = None
    user_id: int | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_expiry: datetime | None = None
    provider_profile_image_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at: datetime | None = None

    def update_tokens(self, access_token: str, refresh_token: str | None = None, expires_at: datetime | None = None) -> None:
        """トークン情報を更新する"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = expires_at
        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def __repr__(self):
        return (
            f'SocialAccountEntity(id={self.id}, provider={self.provider}, '
            f'provider_user_id={self.provider_user_id}, provider_email={self.provider_email}, '
            f'user_id={self.user_id}, access_token={self.access_token}, '
            f'refresh_token={self.refresh_token}, token_expiry={self.token_expiry}, '
            f'provider_profile_image_url={self.provider_profile_image_url}, '
            f'created_at={self.created_at}, updated_at={self.updated_at})'
        )
