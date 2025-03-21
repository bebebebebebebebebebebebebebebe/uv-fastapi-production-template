from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.app.core.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = settings.postgres_async_uri

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_async() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as db:
        yield db
