from fastapi import APIRouter, Depends, HTTPException, Request

from src.app.core.config import settings
from src.app.core.db.database import AsyncSession, get_db_async
from src.app.crud.user_crud import UserCRUD
from src.app.schemas.token_schemas import TokenUserData
from src.app.schemas.user_schemas import CreateInternalUser, ReadUser
from src.app.services.token_service import token_service
from src.app.services.user_service import get_hashed_password
from src.app.worker import tasks
from src.utils.logger import get_logger

from .dependencies import get_current_user
from .schemas import DataInUser

logger = get_logger(__name__)
router = APIRouter(prefix='/users', tags=['users'])


@router.post('/register', response_model=ReadUser, status_code=201)
async def register_user(request: Request, user: DataInUser, db: AsyncSession = Depends(get_db_async)) -> dict[str, str]:
    crud_user = UserCRUD(db)
    email_row = await crud_user.email_exists_async(email=user.email)
    if email_row:
        raise HTTPException(status_code=400, detail='Email already exists')

    user_internal_dict = user.model_dump()
    user_internal_dict['hashed_password'] = get_hashed_password(user.password)
    del user_internal_dict['password']
    logger.info(user_internal_dict)
    user_internal = CreateInternalUser(**user_internal_dict)
    created_user = await crud_user.create_async(user_internal)
    token_data = TokenUserData(id=created_user.id, email=created_user.email)
    verification_token = token_service.create_email_verification_token(token_data)
    verification_url = f'{settings.get_app_url}/api/v1/auth/verify-email?token={verification_token}'
    tasks.send_verify_email.delay(to_email=created_user.email, link=verification_url)

    return created_user


@router.get('/me', response_model=ReadUser)
async def read_users_me(request: Request, current_user: ReadUser = Depends(get_current_user)):
    return current_user
