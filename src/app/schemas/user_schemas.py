from pydantic import BaseModel

from .global_schemas import PersistentDeletion, TimeStampSchema, UUIDSchema


class InternalUser(UUIDSchema, TimeStampSchema, PersistentDeletion):
    id: int
    name: str
    username: str
    email: str
    is_verified: bool
    hashed_password: str


class CreateInternalUser(BaseModel):
    name: str
    username: str
    email: str
    hashed_password: str
    is_verified: bool = False


class ReadUser(UUIDSchema, TimeStampSchema, PersistentDeletion):
    id: int
    name: str
    username: str
    email: str
    is_verified: bool
