from abc import ABC, abstractmethod

import bcrypt


class PasswordService(ABC):
    """
    パスワード操作のためのドメインサービスインターフェース。
    パスワードのハッシュ化と検証を行う機能を定義します。
    """

    @abstractmethod
    def hash_password(self, plain_password: str) -> str:
        """
        平文パスワードをハッシュ化します。

        Args:
            plain_password (str): ハッシュ化する平文パスワード

        Returns:
            str: ハッシュ化されたパスワード
        """
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        平文パスワードがハッシュ化されたパスワードと一致するかを検証します。

        Args:
            plain_password (str): 検証する平文パスワード
            hashed_password (str): 比較対象のハッシュ化されたパスワード

        Returns:
            bool: パスワードが一致する場合はTrue、それ以外はFalse
        """
        pass


class BcryptPasswordService(PasswordService):
    """
    Bcryptを使用したパスワード操作のためのドメインサービス実装。
    """

    def hash_password(self, plain_password: str) -> str:
        """
        平文パスワードをハッシュ化します。
        Args:
            plain_password (str): ハッシュ化する平文パスワード
            Returns:
            str: ハッシュ化されたパスワード
        """
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return hashed_password

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        平文パスワードがハッシュ化されたパスワードと一致するかを検証します。
        Args:
            plain_password (str): 検証する平文パスワード
            hashed_password (str): 比較対象のハッシュ化されたパスワード
            Returns:
            bool: パスワードが一致する場合はTrue、それ以外はFalse
        """
        is_valid = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        return is_valid
