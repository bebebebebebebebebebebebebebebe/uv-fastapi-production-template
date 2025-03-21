from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from jose import jwt
from src.app.core.config import settings
from src.app.domains.token.services.token_service import InvalidTokenException
from src.app.infrastructures.token.services.jwt_token_service import JWTTokenService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TestJWTTokenService:
    @pytest.fixture
    def token_service(self):
        return JWTTokenService(secret_key=settings.SECRET_KEY)

    @pytest.fixture
    def user_id(self):
        # テスト用のユーザーIDを返す
        return 'test_user_id'

    @pytest.fixture
    def email(self):
        # テスト用のメールアドレスを返す
        return 'test@example.com'

    def test_create_access_token_returns_valid_jwt(self, token_service: JWTTokenService, user_id: str, email: str):
        # access_tokenを作成し、正当なJWTが返されることを確認する
        access_token = token_service.create_access_token(user_id, email)
        assert access_token is not None
        # 有効期限が設定されていることを確認する
        payload = jwt.decode(access_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert 'exp' in payload
        assert 'iat' in payload
        assert payload['exp'] - payload['iat'] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 分を秒数に変換して比較
        # ユーザーIDが正しく設定されていることを確認する
        assert payload['sub'] == user_id
        # メールアドレスが正しく設定されていることを確認する
        assert payload['email'] == email
        # ロールが正しく設定されていることを確認する
        assert payload['role'] == 'user'

    def test_create_access_token_without_email(self, token_service: JWTTokenService, user_id: str):
        # メールアドレスを指定しない場合、デフォルト値が設定されていることを確認する
        access_token = token_service.create_access_token(user_id)
        assert access_token is not None
        payload = jwt.decode(access_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['email'] is None
        assert payload['role'] == 'user'
        assert payload['sub'] == user_id
        assert payload['exp'] - payload['iat'] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 分を秒数に変換して比較
        assert payload['iat'] is not None

    def test_create_access_token_with_custom_expiry(self, token_service: JWTTokenService, user_id: str, email: str):
        # 有効期限をカスタマイズしてaccess_tokenを作成し、正当なJWTが返されることを確認する
        access_token = token_service.create_access_token(user_id, email, expires_delta=timedelta(minutes=30))
        assert access_token is not None
        # 有効期限が30分後に設定されていることを確認する
        payload = jwt.decode(access_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['exp'] - payload['iat'] == 30 * 60  # 30分を秒数に変換して比較

    def test_create_access_token_with_admin_role(self, token_service: JWTTokenService, user_id: str, email: str):
        # 管理者権限を持つaccess_tokenを作成し、正当なJWTが返されることを確認する
        access_token = token_service.create_access_token(user_id, email, role='admin')
        assert access_token is not None
        # ペイロードに管理者権限が含まれていることを確認する
        payload = jwt.decode(access_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['role'] == 'admin'

    def test_create_refresh_token_returns_valid_jwt(self, token_service: JWTTokenService, user_id: str):
        # refresh_tokenを作成し、正当なJWTが返されることを確認する
        refresh_token = token_service.create_refresh_token(user_id)
        assert refresh_token is not None
        # 有効期限が7日後に設定されていることを確認する
        payload = jwt.decode(refresh_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['exp'] - payload['iat'] == settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 7日を秒数に変換して比較
        # ユーザーIDが正しく設定されていることを確認する
        assert payload['sub'] == user_id

    def test_create_refresh_token_with_custom_expiry(self, token_service: JWTTokenService, user_id: str):
        # 有効期限をカスタマイズしてrefresh_tokenを作成し、正当なJWTが返されることを確認する
        refresh_token = token_service.create_refresh_token(user_id, expires_delta=timedelta(days=14))
        assert refresh_token is not None
        # 有効期限が14日後に設定されていることを確認する
        payload = jwt.decode(refresh_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['exp'] - payload['iat'] == 14 * 24 * 60 * 60  # 14日を秒数に変換して比較

    def test_create_email_verification_token_returns_valid_jwt(self, token_service: JWTTokenService, user_id: str, email: str):
        # email_verification_tokenを作成し、正当なJWTが返されることを確認する
        email_verification_token = token_service.create_email_verification_token(user_id, email)
        assert email_verification_token is not None
        # 有効期限が15分後に設定されていることを確認する
        payload = jwt.decode(email_verification_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['exp'] - payload['iat'] == settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES * 60
        # ユーザーIDが正しく設定されていることを確認する
        assert payload['sub'] == user_id
        # メールアドレスが正しく設定されていることを確認する
        assert payload['email'] == email

    def test_create_email_verification_token_with_custom_expiry(self, token_service: JWTTokenService, user_id: str, email: str):
        # 有効期限をカスタマイズしてemail_verification_tokenを作成し、正当なJWTが返されることを確認する
        email_verification_token = token_service.create_email_verification_token(user_id, email, expires_delta=timedelta(minutes=30))
        assert email_verification_token is not None
        # 有効期限が30分後に設定されていることを確認する
        payload = jwt.decode(email_verification_token, token_service.secret_key, algorithms=[token_service.algorithm])
        assert payload['exp'] - payload['iat'] == 30 * 60  # 30分を秒数に変換して比較

    def test_verify_token_with_valid_token(self, token_service: JWTTokenService, user_id: str):
        # 有効なトークンを検証し、ペイロードが正しく取得できることを確認する
        access_token = token_service.create_access_token(user_id)
        payload = token_service.verify_token(access_token)
        assert payload is not None
        assert payload['sub'] == user_id
        assert payload['role'] == 'user'
        assert payload['email'] is None
        assert payload['exp'] is not None
        assert payload['iat'] is not None

    def test_verify_token_with_expired_token(self, token_service: JWTTokenService, user_id: str, fixed_time: datetime):
        # 有効期限切れのトークンを検証し、例外が発生することを確認する
        access_token = token_service.create_access_token(user_id)
        with freeze_time(fixed_time + timedelta(days=1)):
            with pytest.raises(InvalidTokenException):
                token_service.verify_token(access_token)

    def test_verify_token_with_invalid_token(self, token_service: JWTTokenService, user_id: str):
        # 無効なトークンを検証し、例外が発生することを確認する
        with pytest.raises(InvalidTokenException):
            token_service.verify_token('invalid_token')

    def test_verify_token_with_tampered_token(self, token_service: JWTTokenService, user_id: str):
        # 改ざんされたトークンを検証し、例外が発生することを確認する
        access_token = token_service.create_access_token(user_id)
        tampered_token = access_token[:-1] + 'X'  # トークンの最後の文字を変更
        with pytest.raises(InvalidTokenException):
            token_service.verify_token(tampered_token)

    def test_token_creation_uses_current_time(self, token_service: JWTTokenService, user_id: str, fixed_time: datetime):
        # トークン作成時に現在時刻が使用されていることを確認する
        with freeze_time(fixed_time):
            access_token = token_service.create_access_token(user_id)
            payload = token_service.verify_token(access_token)
            assert payload['iat'] == fixed_time.timestamp()

    def test_token_expiry_calculation(self, token_service: JWTTokenService, user_id: str, fixed_time: datetime):
        # トークンの有効期限が正しく計算されていることを確認する
        with freeze_time(fixed_time):
            access_token = token_service.create_access_token(user_id)
            payload = token_service.verify_token(access_token)
        assert payload['exp'] == (fixed_time + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
