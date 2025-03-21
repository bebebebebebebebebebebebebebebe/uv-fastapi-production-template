import re
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator


class FullName(BaseModel):
    first_name: str
    last_name: str
    model_config = ConfigDict(frozen=True, extra='forbid')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Email(BaseModel):
    email: str
    EMAIL_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    model_config = ConfigDict(frozen=True, extra='forbid')

    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        if not re.match(cls.EMAIL_PATTERN, v):
            raise ValueError('有効なメールアドレスを入力してください。')
        return v


class Password(BaseModel):
    password: str
    PASSWORD_PATTERN: ClassVar[re.Pattern] = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$')
    model_config = ConfigDict(frozen=True, extra='forbid')

    @field_validator('password')
    def validate_password(cls, v: str) -> str:
        if not re.match(cls.PASSWORD_PATTERN, v):
            raise ValueError('パスワードは8文字以上で、大文字、小文字、数字を含む必要があります。')
        return v


class ProfileImageURL(BaseModel):
    profile_image_url: str
    model_config = ConfigDict(frozen=True, extra='forbid')
    URL_PATTERN: ClassVar[re.Pattern] = re.compile(
        r'^(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))\.(?i:(?:jpg|jpeg|png|gif|webp))$'
    )

    @field_validator('profile_image_url')
    def validate_profile_image_url(cls, v: str) -> str:
        if not re.match(cls.URL_PATTERN, v):
            raise ValueError('有効なURLを入力してください。')
        return v
