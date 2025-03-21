from abc import ABC, abstractmethod

from src.app.domains.oauth.schemas.oauth_schemas import OAuthProviderType, OAuthToken, OAuthUserInfo


class OAuthService(ABC):
    """
    OAuth認証のためのドメインサービスインターフェース。
    OAuth認証に関するドメインロジックを提供します。
    """

    @property
    @abstractmethod
    def provider_type(self) -> OAuthProviderType:
        """
        このサービスが対応するOAuthプロバイダーのタイプを返します。
        """

    @abstractmethod
    def get_authorization_url(self) -> str:
        """
        OAuthプロバイダーの認証画面へのリダイレクトURLを生成します。
        ユーザーがアクセスすると、プロバイダーの認証画面に遷移します。

        Returns:
            str: 認証URLを返します。
        """

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> OAuthToken:
        """
        認証コードをトークンに交換します。

        Args:
            code (str): 認証コード。

        Returns:
            OAuthToken: 交換されたトークン。
        """

    @abstractmethod
    async def get_user_info(self, token: OAuthToken) -> OAuthUserInfo:
        """
        トークンからユーザー情報を取得します。
        このメソッドは、OAuthプロバイダーのAPIを呼び出してユーザー情報を取得します。

        Args:
            token (OAuthToken): ユーザー情報を取得するためのトークン。
        Returns:
            OAuthUserInfo: ユーザー情報。
        """

    @abstractmethod
    async def refresh_oauth_token(self, refresh_token: str) -> OAuthToken | None:
        """
        リフレッシュトークンを使用して新しいアクセストークンを取得します。

        Args:
            refresh_token (str): リフレッシュトークン。
        Returns:
            OAuthToken | None: 新しいOAuthトークン。リフレッシュに失敗した場合はNone。
        """
