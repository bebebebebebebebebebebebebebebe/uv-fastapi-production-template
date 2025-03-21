from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from src.app.models.user import User
from src.app.schemas.user_schemas import CreateInternalUser, ReadUser
from src.app.services.user_service import verify_password
from src.utils.logger import get_logger

from .base_crud import SQLAlchemyCRUD

logger = get_logger(__name__)


class UserCRUD(SQLAlchemyCRUD[CreateInternalUser, ReadUser]):
    def __init__(self, db_session: Session | AsyncSession):
        super().__init__(db_session, User, ReadUser)

    def _prepare_data(self, obj_in):
        return {
            'name': obj_in.name,
            'username': obj_in.username,
            'email': obj_in.email,
            'hashed_password': obj_in.hashed_password,
        }

    def email_exists(self, email: str) -> bool:
        results = self.read_by_filter(email=email)
        return len(results) > 0

    async def email_exists_async(self, email: str) -> bool:
        results = await self.read_by_filter_async(email=email)
        return len(results) > 0

    async def username_exists_async(self, username: str) -> bool:
        """指定されたユーザー名が既に存在するかどうかを非同期的に確認する"""
        results = await self.read_by_filter_async(username=username)
        return len(results) > 0

    async def get_by_email_async(self, email: str) -> ReadUser | None:
        results = await self.read_by_filter_async(email=email)
        if not results:
            logger.error(f'User not found with email: {email}')
            return None
        return results[0]

    async def get_by_id_async(self, id: int) -> ReadUser | None:
        """指定されたIDのユーザーを非同期的に取得する"""
        return await self.read_async(id)

    async def update_verified(self, id: int) -> ReadUser | None:
        session = self._check_async_session()
        query = select(User).where(User.id == id)
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            logger.error(f'User not found: {user}')
            return None
        user.is_verified = True
        await session.commit()
        await session.refresh(user)
        return self._convert_to_pydantic_model(user)

    async def authenticate(self, email: str, password: str) -> ReadUser | None:
        session = self._check_async_session()
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            logger.error(f'User not found: {user}')
            return None
        if not verify_password(password, user.hashed_password):
            logger.error('Password verification failed')
            return None
        return self._convert_to_pydantic_model(user)
