from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from src.app.crud.base_crud import SQLAlchemyCRUD
from src.app.models.social_account import SocialAccount
from src.app.schemas.social_account_schema import CreateInternalSocialAccount, ReadSocialAccount


class SocialAccountCRUD(SQLAlchemyCRUD[CreateInternalSocialAccount, ReadSocialAccount]):
    def __init__(self, db_session):
        super().__init__(db_session, SocialAccount, ReadSocialAccount)

    async def get_by_provider_and_id(self, provider: str, provider_user_id: str) -> ReadSocialAccount | None:
        """指定されたプロバイダーとプロバイダーユーザーIDでSocialAccountを取得"""
        session = self._check_async_session()
        query = select(self.db_model).where(self.db_model.provider == provider, self.db_model.provider_user_id == provider_user_id)
        result = await session.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            return self._convert_to_pydantic_model(db_obj)
        return None

    async def get_by_user_id(self, user_id: int) -> list[ReadSocialAccount]:
        """指定されたユーザーIDでSocialAccountを取得"""
        session = self._check_async_session()
        query = select(self.db_model).where(self.db_model.user_id == user_id)
        result = await session.execute(query)
        db_objs = result.scalars().all()
        return [self._convert_to_pydantic_model(db_obj) for db_obj in db_objs]

    async def update_tokens(
        self,
        social_account_id: int,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
    ) -> ReadSocialAccount | None:
        """指定されたSocialAccountのトークンを更新"""
        session = self._check_async_session()
        query = select(self.db_model).where(self.db_model.id == social_account_id)
        result = await session.execute(query)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None

        db_obj.access_token = access_token
        db_obj.refresh_token = refresh_token
        db_obj.token_expiry = token_expiry
        db_obj.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        await session.commit()
        await session.refresh(db_obj)
        return self._convert_to_pydantic_model(db_obj)

    async def delete_by_user_id_and_provider(self, user_id: int, provider: str) -> bool:
        """指定されたユーザーIDとプロバイダーでSocialAccountを削除"""
        session = self._check_async_session()
        query = select(self.db_model).where(self.db_model.user_id == user_id, self.db_model.provider == provider)
        result = await session.execute(query)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False

        await session.delete(db_obj)
        await session.commit()
        return True
