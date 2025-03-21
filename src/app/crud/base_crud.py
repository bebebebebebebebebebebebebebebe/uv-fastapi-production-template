import abc
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from src.app.models.base_model import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')  # 入力型
U = TypeVar('U')  # 出力型


class CRUDException(Exception):
    pass


class CRUDInterface(abc.ABC, Generic[T, U]):
    """CRUD操作の汎用インターフェースクラス"""

    @abc.abstractmethod
    def create(self, obj_in: T) -> U:
        """同期的なデータ作成処理"""
        ...

    @abc.abstractmethod
    async def create_async(self, obj_in: T) -> U:
        """非同期的なデータ作成処理"""
        ...

    @abc.abstractmethod
    def read(self, id: int) -> U | None:
        """同期的にデータを1件取得"""
        ...

    @abc.abstractmethod
    async def read_async(self, id: int) -> U | None:
        """非同期的にデータを1件取得"""
        ...

    @abc.abstractmethod
    def read_by_filter(self, **filters) -> list[U]:
        """任意のフィルタ条件でデータを取得（同期）"""
        ...

    @abc.abstractmethod
    async def read_by_filter_async(self, **filters) -> list[U]:
        """任意のフィルタ条件でデータを取得（非同期）"""

    @abc.abstractmethod
    def read_all(self, filters: dict[str, Any] | None = None) -> list[U]:
        """同期的にデータを全件取得"""
        ...

    @abc.abstractmethod
    async def read_all_async(self, filters: dict[str, Any] | None = None) -> list[U]:
        """非同期的にデータを全件取得"""
        ...

    @abc.abstractmethod
    def update(self, id: int, obj_in: T) -> U | None:
        """同期的にデータを更新"""
        ...

    @abc.abstractmethod
    async def update_async(self, id: int, obj_in: T) -> U | None:
        """非同期的にデータを更新"""
        ...

    @abc.abstractmethod
    def delete(self, id: int) -> None:
        """同期的にデータを削除"""
        ...

    @abc.abstractmethod
    async def delete_async(self, id: int) -> None:
        """非同期的にデータを削除"""
        ...

    def _model_to_dict(self, obj_in: T) -> dict[str, Any]:
        """pydanticモデルを辞書に変換"""
        if isinstance(obj_in, dict):
            return obj_in

        if isinstance(obj_in, BaseModel):
            return obj_in.model_dump()
        raise CRUDException(f'Unsupported type: {type(obj_in)}')


class SQLAlchemyCRUD(CRUDInterface[T, U], abc.ABC, Generic[T, U]):
    """SQLAlchemyを使用したCRUD操作の抽象クラス"""

    def __init__(
        self,
        db_session: Session | AsyncSession,
        db_model: type[T],
        output_model: type[U],
    ):
        """:param db_session: SQLAlchemyのセッション (同期または非同期)
        :param model: 操作対象のSQLAlchemyモデル
        """
        self.db_session = db_session
        self.db_model = db_model
        self.output_model = output_model

    def _prepare_data(self, obj_in: T) -> dict[str, Any]:
        """データ作成時にカスタム処理を適用できるメソッド
        サブクラスでオーバーライドする
        """
        return self._model_to_dict(obj_in)

    def _convert_to_pydantic_model(self, obj: Base) -> U:
        """SQLAlchemyモデルをPydanticモデルに変換"""
        data = {}

        for field in self.output_model.model_fields:
            value = getattr(obj, field)
            data[field] = value

        return self.output_model.model_validate(data)

    def _check_sync_session(self) -> Session:
        if not isinstance(self.db_session, Session):
            raise CRUDException('Sync session is required for this method.')
        return self.db_session

    def _check_async_session(self) -> AsyncSession:
        if not isinstance(self.db_session, AsyncSession):
            raise CRUDException('Async session is required for this method.')
        return self.db_session

    def create(self, obj_in: T) -> U:
        """同期的にデータを作成"""
        session = self._check_sync_session()
        obj_data = self._prepare_data(obj_in)
        obj = self.db_model(**obj_data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return self._convert_to_pydantic_model(obj)

    async def create_async(self, obj_in: T) -> U:
        """非同期的にデータを作成"""
        session = self._check_async_session()
        obj_data = self._prepare_data(obj_in)
        obj = self.db_model(**obj_data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return self._convert_to_pydantic_model(obj)

    def read(self, id: int) -> U | None:
        """同期的にデータを取得し、Pydanticモデルで返却"""
        session = self._check_sync_session()
        obj = session.query(self.db_model).filter(self.db_model.id == id).one_or_none()
        if obj:
            return self._convert_to_pydantic_model(obj)
        return None

    async def read_async(self, id: int) -> U | None:
        """非同期的にデータを取得し、Pydanticモデルで返却"""
        session = self._check_async_session()
        result = await session.execute(select(self.db_model).where(self.db_model.id == id))
        obj = result.scalar_one_or_none()
        if obj:
            return self._convert_to_pydantic_model(obj)
        return None

    def read_by_filter(self, **filters) -> list[U]:
        """任意のフィルタ条件でデータを取得（同期）し、Pydanticモデルで返却"""
        session = self._check_sync_session()
        query = session.query(self.db_model).filter_by(**filters)
        results = query.all()
        return [self._convert_to_pydantic_model(obj) for obj in results]

    async def read_by_filter_async(self, **filters) -> list[U]:
        """任意のフィルタ条件でデータを取得（非同期）し、Pydanticモデルで返却"""
        session = self._check_async_session()
        query = select(self.db_model).filter_by(**filters)
        result = await session.execute(query)
        objs = result.scalars().all()
        return [self._convert_to_pydantic_model(obj) for obj in objs]

    def read_all(self, filters: dict[str, Any] | None = None) -> list[U]:
        """同期的に全データを取得し、Pydanticモデルで返却"""
        session = self._check_sync_session()
        query = session.query(self.db_model)
        if filters:
            query = query.filter_by(**filters)
        results = query.all()
        return [self._convert_to_pydantic_model(obj) for obj in results]

    async def read_all_async(self, filters: dict[str, Any] | None = None) -> list[U]:
        """非同期的に全データを取得し、Pydanticモデルで返却"""
        session = self._check_async_session()
        query = select(self.db_model)
        if filters:
            query = query.filter_by(**filters)
        result = await session.execute(query)
        objs = result.scalars().all()
        return [self._convert_to_pydantic_model(obj) for obj in objs]

    def update(self, id: int, obj_in: T) -> U | None:
        """同期的にデータを更新"""
        session = self._check_sync_session()
        obj = self.read(id)
        if not obj:
            return None
        for key, value in obj_in.dict().items():
            setattr(obj, key, value)
        session.commit()
        session.refresh(obj)
        return self._convert_to_pydantic_model(obj)

    async def update_async(self, id: int, obj_in: T) -> U | None:
        """非同期的にデータを更新"""
        session = self._check_async_session()
        obj = await self.read_async(id)
        if not obj:
            return None
        for key, value in obj_in.dict().items():
            setattr(obj, key, value)
        await session.commit()
        await session.refresh(obj)
        return self._convert_to_pydantic_model(obj)

    def delete(self, id: int) -> None:
        """同期的にデータを削除"""
        session = self._check_sync_session()
        obj = self.read(id)
        if not obj:
            raise CRUDException(f'Object with ID {id} does not exist.')
        session.delete(obj)
        session.commit()

    async def delete_async(self, id: int) -> None:
        """非同期的にデータを削除"""
        session = self._check_async_session()
        obj = await self.read_async(id)
        if not obj:
            raise CRUDException(f'Object with ID {id} does not exist.')
        session.delete(obj)
        await session.commit()
