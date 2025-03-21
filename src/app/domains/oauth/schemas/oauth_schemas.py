# /domains/auth/schemas/oauth_schemas.py
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict


class OAuthProviderType(str, Enum):
    """OAuthプロバイダータイプ"""

    GOOGLE = 'google'
    GITHUB = 'github'


class OAuthToken(BaseModel):
    """
    OAuth認証トークンを表す値オブジェクト。

    Attributes:
        access_token (str): アクセス認証に使用されるトークン。
        refresh_token (Optional[str]): アクセストークンが期限切れの場合に使用されるリフレッシュトークン。
        id_token (Optional[str]): OpenID Connect のIDトークン（Googleなどで使用）。
        token_type (str): トークンの種類。通常は "Bearer"。
        expires_at (Optional[datetime]): アクセストークンの有効期限。
        scope (Optional[str]): トークンに付与されたアクセススコープ。
    """

    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None  # ID トークンを追加
    token_type: str = 'Bearer'
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @classmethod
    def create(
        cls,
        access_token: str,
        refresh_token: Optional[str] = None,
        id_token: Optional[str] = None,  # ID トークンパラメータを追加
        token_type: str = 'Bearer',
        expires_in: Optional[int] = None,
        scope: Optional[str] = None,
    ) -> 'OAuthToken':
        """
        OAuthトークンを生成するファクトリメソッド。

        Args:
            access_token (str): アクセス認証に使用されるトークン。
            refresh_token (Optional[str]): リフレッシュトークン。
            id_token (Optional[str]): OpenID Connect のIDトークン。
            token_type (str): トークンの種類。デフォルトは 'Bearer'。
            expires_in (Optional[int]): トークンの有効期間（秒単位）。
            scope (Optional[str]): トークンに付与されたアクセススコープ。

        Returns:
            OAuthToken: 生成されたOAuthトークンオブジェクト。
        """
        expires_at = None
        if expires_in:
            expires_at = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + timedelta(seconds=expires_in)
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,  # ID トークンを設定
            token_type=token_type,
            expires_at=expires_at,
            scope=scope,
        )

    def is_expired(self, reference_time: Optional[datetime] = None) -> bool:
        """
        トークンが有効期限切れかどうかをチェックするメソッド。
        引数には現在時刻を渡すことができる。
        引数がない場合は現在時刻を使用する。

        Args:
            reference_time (Optional[datetime]): 参照時刻。デフォルトは現在時刻。'

        Returns:
            bool: トークンが有効期限切れの場合はTrue、それ以外はFalse。
        """

        if not self.expires_at:
            return False

        now = reference_time or datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        return now > self.expires_at


class OAuthUserInfo(BaseModel):
    """OAuthプロバイダーから取得したユーザー情報"""

    provider: OAuthProviderType
    provider_user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None

    model_config = ConfigDict(frozen=True)
