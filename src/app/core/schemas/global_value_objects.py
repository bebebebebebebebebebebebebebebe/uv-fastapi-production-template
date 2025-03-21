from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class DateTimeValue(BaseModel):
    """日時を表現する基本的な値オブジェクト"""

    value: datetime

    model_config = ConfigDict(frozen=True)  # 不変性の確保

    @field_serializer('value')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)


class EntityUUID(BaseModel):
    """エンティティのUUIDを表現する値オブジェクト"""

    value: UUID

    model_config = ConfigDict(frozen=True)

    @classmethod
    def generate(cls) -> 'EntityUUID':
        """新しいUUIDを生成する"""
        return cls(value=uuid4())

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return str(self.value)


# エンティティに組み込むための特性クラス（ミックスイン）
class TimestampedMixin(BaseModel):
    """タイムスタンプ機能を提供するミックスイン"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at: Optional[datetime] = None

    def update_timestamp(self) -> None:
        """更新日時を現在時刻に設定"""
        self.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    @field_serializer('created_at', 'updated_at')
    def serialize_dates(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class LogicalDeletionMixin(BaseModel):
    """論理削除機能を提供するミックスイン"""

    deleted_at: Optional[datetime] = None
    is_deleted: bool = False

    def mark_as_deleted(self) -> None:
        """エンティティを論理削除としてマーク"""
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def restore(self) -> None:
        """論理削除を取り消す"""
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None

    @field_serializer('deleted_at')
    def serialize_deleted_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None
