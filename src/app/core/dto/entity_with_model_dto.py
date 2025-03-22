from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')  # entity
U = TypeVar('U')  # db model


class EntityWithModelDTO(ABC, Generic[T, U]):
    """
    モデルとドメインエンティティの変換を担当するDTOクラス
    """

    @staticmethod
    @abstractmethod
    def to_entity(model: U) -> T:
        """
        モデルからエンティティを作成します。
        Args:
            model (U): モデル
        Returns:
            T: エンティティ
        """
        pass

    @staticmethod
    @abstractmethod
    def to_model(entity: T) -> U:
        """
        エンティティからモデルを作成します。
        Args:
            entity (T): エンティティ
        Returns:
            U: モデル
        """
        pass
