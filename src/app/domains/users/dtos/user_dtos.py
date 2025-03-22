from pydantic import BaseModel


class CreateInternalUser(BaseModel):
    """
    内部で使用するユーザー作成用のデータ転送オブジェクト。
    """

    username: str
    email: str
    full_name: str | None = None
    hashed_password: str | None = None
    is_verified: bool = False
    profile_image_url: str | None = None


class UpdateInternalUser(BaseModel):
    """
    内部で使用するユーザー更新用のデータ転送オブジェクト。
    """

    id: int
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    hashed_password: str | None = None
    is_verified: bool | None = None
    profile_image_url: str | None = None
