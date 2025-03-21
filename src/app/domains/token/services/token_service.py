from abc import ABC, abstractmethod
from datetime import timedelta


class InvalidTokenException(Exception):
    """
    無効なトークンが検出された場合にスローされる例外。
    """

    pass


class TokenService(ABC):
    """
    トークンサービスの抽象基底クラス。
    トークンの生成、検証、およびリフレッシュを行うためのメソッドを提供します。
    """

    @abstractmethod
    def create_access_token(
        self, user_id: str, email: str | None = None, role: str = 'user', expires_delta: timedelta = timedelta(minutes=15)
    ) -> str:
        """
        アクセストークンを生成します。
        アクセストークンは、ユーザーの識別に使用されます。

        Args:
            user_id (str): トークンに含まれるユーザーID。
            email (str): ユーザーのメールアドレス。 デフォルトは None。
            role (str): トークンのスコープ。デフォルトは "user"。
            expires_delta (timedelta): トークンの有効期限。デフォルトは 15 分。

        returns:
            str: 生成されたアクセストークン。
        """
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: str, expires_delta: timedelta = timedelta(days=7)) -> str:
        """
        リフレッシュトークンを生成します。
        リフレッシュトークンは、アクセストークンの有効期限切れ時に使用されます。

        Args:
            user_id (str): トークンに含まれるユーザーID。"。
            expires_delta (timedelta): トークンの有効期限。デフォルトは 7 日。
        returns:
            str: 生成されたリフレッシュトークン。
        """
        pass

    @abstractmethod
    def create_email_verification_token(
        self, user_id: str, email: str | None = None, expires_delta: timedelta = timedelta(minutes=15)
    ) -> str:
        """
        メールアドレス確認用のトークンを生成します。
        このトークンは、ユーザーのメールアドレスを確認するために使用されます。

        Args:
            user_id (str): トークンに含まれるユーザーID。
            email (str): ユーザーのメールアドレス。 デフォルトは None。
            expires_delta (timedelta): トークンの有効期限。デフォルトは 15 分。
        returns:
            str: 生成されたメールアドレス確認用トークン。
        """
        pass

    @abstractmethod
    def verify_token(self, token: str) -> dict[str, any]:
        """
        トークンを検証します。
        トークンが有効であれば、ユーザー情報を返します。

        """
        pass
