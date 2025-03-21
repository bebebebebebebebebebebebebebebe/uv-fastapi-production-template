from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserRegistrationRequest(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    profile_image_url: str | None


class OAuthUserRegistrationRequest(BaseModel):
    provider: str
    provider_user_id: str
    email: str
    username: str
    profile_image_url: str | None


class UserResponse(BaseModel):
    id: int
    uuid: UUID
    full_name: str
    username: str
    email: str
    is_verified: bool
    profile_image_url: str | None
    created_at: datetime
    updated_at: datetime | None
