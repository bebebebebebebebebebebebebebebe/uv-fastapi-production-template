import uuid as uuid_pkg
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_serializer


class UUIDSchema(BaseModel):
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)


class TimeStampSchema(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at: datetime | None = Field(default=None)

    @field_serializer('created_at', 'updated_at')
    def serialize_dates(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None


class PersistentDeletion(BaseModel):
    deleted_at: datetime | None = Field(default=None)
    is_deleted: bool = False

    @field_serializer('deleted_at')
    def serialize_dates(self, deleted_at: datetime | None) -> str | None:
        if deleted_at is not None:
            return deleted_at.isoformat()

        return None
