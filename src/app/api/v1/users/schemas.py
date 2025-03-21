import re
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataInUser(BaseModel):
    name: str
    username: str
    email: str
    password: str = Field(
        examples=['Password123!'],
    )

    PASSWORD_PATTERN: ClassVar[re.Pattern] = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$')
    model_config = ConfigDict(extra='forbid')

    @classmethod
    @field_validator('password')
    def validate_password(cls, v: str) -> str:
        if not re.match(cls.PASSWORD_PATTERN, v):
            raise ValueError('パスワードは8文字以上で、大文字、小文字、数字を含む必要があります。')
        return v


class ResponseUser(BaseModel):
    id: int
    name: str
    username: str
    email: str
    created_at: str
    updated_at: str | None
    deleted_at: str | None
    is_deleted: bool = False
