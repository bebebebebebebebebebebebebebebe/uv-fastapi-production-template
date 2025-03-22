import uuid as uuid_pkg
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base
from .social_account import SocialAccount


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column('id', autoincrement=True, primary_key=True, unique=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        unique=True,
    )
    full_name: Mapped[str | None] = mapped_column(String(50), default=None, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    is_verified: Mapped[bool] = mapped_column(default=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)
    social_accounts = relationship(SocialAccount, back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f'User(id={self.id!r}, full_name={self.full_name!r}, username={self.username!r}, email={self.email!r})'


# class User(Base):
#     __tablename__ = 'users'
#     id: Mapped[int] = mapped_column('id', autoincrement=True, primary_key=True, unique=True, init=False)
#     name: Mapped[str] = mapped_column(String(50))
#     username: Mapped[str] = mapped_column(String(50), unique=True)
#     email: Mapped[str] = mapped_column(String(100), unique=True)
#     hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
#     is_verified: Mapped[bool] = mapped_column(default=False)
#     uuid: Mapped[uuid_pkg.UUID] = mapped_column(
#         default_factory=uuid_pkg.uuid4,
#         unique=True,
#     )
#     profile_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default_factory=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')),
#     )
#     updated_at: Mapped[datetime | None] = mapped_column(
#         DateTime(timezone=True),
#         default=None,
#     )
#     deleted_at: Mapped[datetime | None] = mapped_column(
#         DateTime(timezone=True),
#         default=None,
#     )
#     is_deleted: Mapped[bool] = mapped_column(default=False)
#     social_accounts = relationship(SocialAccount, back_populates='user', cascade='all, delete-orphan')

#     def __repr__(self):
#         return f'User(id={self.uuid!r}, name={self.name!r}, username={self.username!r}, email={self.email!r})'
