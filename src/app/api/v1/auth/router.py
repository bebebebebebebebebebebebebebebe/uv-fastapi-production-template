from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.db.database import get_db_async
from src.app.crud.social_account_crud import SocialAccountCRUD
from src.app.crud.user_crud import UserCRUD
from src.app.schemas.social_account_schema import CreateInternalSocialAccount
from src.app.schemas.token_schemas import TokenUserData
from src.app.schemas.user_schemas import CreateInternalUser
from src.app.services.token_service import token_service
from src.utils.logger import get_logger

from .schemas import LogoutResponse, TokenResponse

logger = get_logger(__name__)
router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_async),
) -> dict[str, str]:
    user_crud = UserCRUD(db)
    user = await user_crud.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        response.status_code = 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='メールアドレスまたはパスワードが正しくありません。',
        )
    token_input_data = TokenUserData(
        id=user.id,
        email=user.email,
    )
    access_token = token_service.create_access_token(
        token_input_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = token_service.create_refresh_token(
        token_input_data,
    )
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        max_age=max_age,
        secure=True,
        samesite='lax',
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/google/login', response_class=RedirectResponse)
async def login_with_google():
    google_auth_url = (
        f'{settings.GOOGLE_AUTH_URL}'
        f'?client_id={settings.GOOGLE_OAUTH_CLIENT_ID}'
        f'&redirect_uri={settings.get_google_redirect_uri}'
        f'&response_type=code'
        f'&scope=openid%20email%20profile'
        f'&access_type=offline'
        f'&prompt=consent'
    )
    return RedirectResponse(google_auth_url)


@router.get('/google/callback', response_class=RedirectResponse)
async def login_with_google_callback(code: str, request: Request, response: Response, db: AsyncSession = Depends(get_db_async)):
    data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'redirect_uri': settings.get_google_redirect_uri,
        'grant_type': 'authorization_code',
    }
    async with httpx.AsyncClient() as client:
        token_response = await client.post(settings.GOOGLE_TOKEN_URL, data=data)
        token_response.raise_for_status()
        token_data = token_response.json()
        logger.info(f'token_data: {token_data}')

    id_token_value = token_data.get('id_token')
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 3600)
    token_expiry = datetime.now(tz=ZoneInfo('Asia/Tokyo')) + timedelta(seconds=expires_in)

    if not id_token_value or not access_token or not refresh_token or not expires_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Googleからのレスポンスに必要な情報が含まれていません。',
        )

    try:
        id_info = id_token.verify_oauth2_token(
            id_token_value,
            requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
        google_user_id = id_info.get('sub')
        email = id_info.get('email')
        name = id_info.get('name', '')
        email_verified = id_info.get('email_verified', False)
        exp = id_info.get('exp')
        picture = id_info.get('picture', '')

        if not google_user_id or not email or not name or not email_verified or not exp or not picture:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Googleからのレスポンスに必要な情報が含まれていません。',
            )

        social_account_crud = SocialAccountCRUD(db)
        user_crud = UserCRUD(db)
        social_account = await social_account_crud.get_by_provider_and_id(
            google_user_id,
            'google',
        )

        if social_account:
            # 既存のソーシャルアカウントがある場合
            logger.info(f'既存のGoogleアカウント連携を検出: {email}')

            user = await user_crud.get_by_id_async(social_account.user_id)

            if not user:
                # ユーザーが見つからない場合（通常は発生しないはず）
                logger.error(f'ソーシャルアカウントに紐づくユーザーが見つかりません: {social_account.user_id}')
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='ユーザーが見つかりません。',
                )

            await social_account_crud.update_tokens(
                social_account_id=social_account.id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
            )

        else:
            # 新しいソーシャルアカウントの場合
            logger.info(f'新しいGoogleアカウント連携を検出: {email}')
            existing_user = await user_crud.get_by_email_async(email)

            if existing_user:
                # 既存のユーザーがある場合
                logger.info(f'既存のユーザーを検出: {email}')
                user = existing_user

            else:
                # 新しいユーザーの場合
                logger.info(f'新しいユーザーを作成: {email}')
                username = email.split('@')[0]

                counter = 1
                while await user_crud.username_exists_async(username):
                    username = f'{username}_{counter}'
                    counter += 1
                logger.info(f'既存のユーザーを検出: {username}')
                user_data = CreateInternalUser(
                    name=name,
                    username=username,
                    email=email,
                    hashed_password='',
                    is_verified=True,
                )
                user = await user_crud.create_async(user_data)
                logger.info(f'ユーザーを作成しました: {user.id}')

            social_account_data = CreateInternalSocialAccount(
                provider='google',
                provider_user_id=google_user_id,
                provider_email=email,
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
            account = await social_account_crud.create_async(social_account_data)
            logger.info(f'ソーシャルアカウントを作成しました: {account.id}')

        # JWTトークンの生成
        token_input_data = TokenUserData(
            id=user.id,
            email=user.email,
        )
        jwt_access_token = token_service.create_access_token(
            token_input_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        jwt_refresh_token = token_service.create_refresh_token(
            token_input_data,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        logger.info(f'アクセストークンを生成しました: {jwt_access_token}')

        max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        response.set_cookie(
            key='refresh_token',
            value=jwt_refresh_token,
            max_age=max_age,
            httponly=True,
            samesite='lax',
            secure=True,
        )
        logger.info(f'リフレッシュトークンをクッキーに設定しました: {jwt_refresh_token}')

        return RedirectResponse('https://www.google.com/')

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=f'エラーが発生しました: {str(e)}')


@router.post('/logout', response_model=LogoutResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias='refresh_token'),
):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='refresh_token is not found.',
        )
    response.delete_cookie(key='refresh_token')
    return {'message': 'Successfully logged out'}


@router.get('/verify-email')
async def verify_email(token: str, db: AsyncSession = Depends(get_db_async)):
    payload = token_service.verify_token(token)
    if not payload:
        detail = 'Invalid or expired token'
        logger.error(detail)
        raise HTTPException(status_code=400, detail=detail)
    user_crud = UserCRUD(db)
    user = await user_crud.get_by_email_async(payload.email)
    if not user:
        detail = f'User not found: {payload.email}'
        logger.error(detail)
        raise HTTPException(status_code=404, detail=detail)
    updated_user = await user_crud.update_verified(user.id)
    if not updated_user:
        detail = 'Failed to update user'
        raise HTTPException(status_code=500, detail=detail)
    return {'message': 'Email verified successfully'}
