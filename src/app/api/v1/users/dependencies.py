from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db.database import get_db_async
from src.app.crud.user_crud import UserCRUD
from src.app.services.auth_service import oauth2_scheme
from src.app.services.token_service import token_service


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_async)):
    crud_user = UserCRUD(db)
    payload = token_service.verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = await crud_user.get_by_email_async(payload.email)
    if user is None:
        raise HTTPException(status_code=401, detail='user not authorized')
    return user
