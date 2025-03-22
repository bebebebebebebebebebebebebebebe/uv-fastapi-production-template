from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from src.app.core.schemas.global_value_objects import EntityUUID
from src.app.domains.social_accounts.entities.social_account_entity import SocialAccountEntity
from src.app.domains.users.schemas.user_schemas import Email, FullName


@dataclass
class UserEntity:
    """ユーザーのエンティティ"""

    id: int
    username: str
    email: Email
    full_name: FullName | None = None
    hashed_password: str | None = None
    is_verified: bool = False
    profile_image_url: str | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    is_deleted: bool = False
    uuid: EntityUUID = field(default_factory=EntityUUID.generate)
    created_at: datetime = field(default_factory=datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    social_accounts: list[SocialAccountEntity] = field(default_factory=list)

    def mark_as_verified(self) -> None:
        """ユーザーを認証済みとしてマーク"""
        self.is_verified = True
        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def update_profile(
        self,
        full_name: FullName | None = None,
        username: str | None = None,
        profile_image_url: str | None = None,
    ) -> None:
        """プロフィール情報を更新する"""
        if full_name is not None:
            self.full_name = full_name
        if username is not None:
            self.username = username
        if profile_image_url is not None:
            self.profile_image_url = profile_image_url

        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def set_password(self, hashed_password: str) -> None:
        """ハッシュ化されたパスワードを設定する"""
        self.hashed_password = hashed_password
        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def add_social_account(self, social_account: SocialAccountEntity) -> None:
        """ソーシャルアカウントを追加する"""
        self.social_accounts.append(social_account)
        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def remove_social_account(self, provider: str, provider_user_id: str) -> None:
        """指定されたプロバイダーのソーシャルアカウントを削除する"""
        self.social_accounts = [
            account
            for account in self.social_accounts
            if not (account.provider == provider and account.provider_user_id == provider_user_id)
        ]
        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def mark_as_deleted(self) -> None:
        """ユーザーを論理削除としてマーク"""
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def restore(self) -> None:
        """論理削除されたユーザーを復元する"""
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def __repr__(self):
        return (
            f'UserEntity(id={self.id}, full_name={self.full_name}, username={self.username}, '
            f'email={self.email}, is_verified={self.is_verified}, uuid={self.uuid}, '
            f'profile_image_url={self.profile_image_url}, created_at={self.created_at}, '
            f'updated_at={self.updated_at}, deleted_at={self.deleted_at}, '
            f'is_deleted={self.is_deleted})'
        )
