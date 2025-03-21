import httpx
from google.auth.transport import requests
from google.oauth2 import id_token

from src.app.core.config import settings
from src.app.domains.oauth.schemas.oauth_schemas import OAuthProviderType, OAuthToken, OAuthUserInfo
from src.app.domains.oauth.services.oauth_service import OAuthService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleOAuthConfigError(Exception):
    """Google OAuthの設定が不正な場合に発生する例外"""

    def __init__(self, missing_fields):
        self.missing_fields = missing_fields
        super().__init__(f"Google OAuthの設定に不備があります: {', '.join(missing_fields)}")


class GoogleOAuthService(OAuthService):
    """
    Google OAuth認証のためのサービスクラス。
    """

    def __init__(
        self,
        client_id: str | None = settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret: str | None = settings.GOOGLE_OAUTH_CLIENT_SECRET,
        auth_url: str | None = settings.GOOGLE_AUTH_URL,
        token_url: str | None = settings.GOOGLE_TOKEN_URL,
        user_info_url: str | None = settings.GOOGLE_USERINFO_URL,
    ):
        """
        Args:

        client_id (str | None, optional): Google OAuthのクライアントID。デフォルトはsettings.GOOGLE_OAUTH_CLIENT_ID
        client_secret (str | None, optional): Google OAuthのクライアントシークレット。デフォルトはsettings.GOOGLE_OAUTH_CLIENT_SECRET
        auth_url (str | None, optional): Google OAuthの認証を行うURL。デフォルトはsettings.GOOGLE_AUTH_URL
        token_url (str | None, optional): Google OAuthのトークン取得エンドポイント。デフォルトはsettings.GOOGLE_TOKEN_URL
        user_info_url (str | None, optional): Google OAuthのユーザー情報取得エンドポイント。デフォルトはsettings.GOOGLE_USERINFO_URL

        Google OAuthの設定が不備な場合、GoogleOAuthConfigError例外を発生させます。
        """

        missing_fields = [
            field_name
            for field_name, field_value in {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_url': auth_url,
                'token_url': token_url,
                'user_info_url': user_info_url,
            }.items()
            if field_value is None
        ]
        if missing_fields:
            raise GoogleOAuthConfigError(missing_fields)

        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.user_info_url = user_info_url
        self.redirect_uri = settings.get_google_redirect_uri

    @property
    def provider_type(self) -> OAuthProviderType:
        return OAuthProviderType.GOOGLE

    def get_authorization_url(self) -> str:
        """
        Google OAuthの認証画面へのリダイレクトURLを生成します。
        ユーザーがアクセスすると、Googleの認証画面に遷移します。

        Returns:
            str: 認証URLを返します。
        """
        return (
            f'{self.auth_url}'
            f'?client_id={self.client_id}'
            f'&redirect_uri={self.redirect_uri}'
            f'&response_type=code'
            f'&scope=openid%20email%20profile'
            f'&access_type=offline'
            f'&prompt=consent'
        )

    async def exchange_code_for_token(self, code: str) -> OAuthToken:
        """
        認証コードをトークンに交換します。

        Args:
            code (str): 認証コード。

        Returns:
            OAuthToken: 交換されたトークン。
        """
        payload = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code',
        }

        async with httpx.AsyncClient() as clinet:
            try:
                token_response = await clinet.post(self.token_url, data=payload)
                token_response.raise_for_status()
                token_data = token_response.json()
                logger.info(f'GoogleOAuthトークンを取得しました: {token_data}')

            except httpx.HTTPStatusError as e:
                logger.error(f'HTTPStatusErrorが発生しました: {e}')
                raise e
            except httpx.RequestError as e:
                logger.error(f'RequestErrorが発生しました: {e}')
                raise e

            id_token = token_data.get('id_token')
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 3600)
            token_type = token_data.get('token_type', 'Bearer')
            scope = token_data.get('scope')

            return OAuthToken.create(
                id_token=id_token,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                token_type=token_type,
                scope=scope,
            )

    async def get_user_info(self, token: OAuthToken) -> OAuthUserInfo:
        """
        トークンからユーザー情報を取得します。
        Args:
            token (OAuthToken): トークン。
        Returns:
            OAuthUserInfo: ユーザー情報。
        """
        if not token.access_token:
            raise ValueError('トークンが存在しません')
        if not token.id_token:
            raise ValueError('IDトークンが存在しません')
        if not token.refresh_token:
            raise ValueError('リフレッシュトークンが存在しません')

        try:
            user_info = id_token.verify_oauth2_token(
                token.id_token,
                requests.Request(),
                self.client_id,
            )

        except Exception as e:
            logger.error(f'IDトークンの検証に失敗しました: {e}')
            raise e

        provider_user_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        return OAuthUserInfo(
            provider=self.provider_type,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
            picture=picture,
        )
