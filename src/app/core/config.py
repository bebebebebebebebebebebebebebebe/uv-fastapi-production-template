from pydantic.fields import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    APP_NAME: str = Field(default='FastAPI Boilerplate')
    APP_VERSION: str = Field(default='0.0.1')
    APP_HOST: str = Field(default='localhost')
    APP_PORT: int = Field(default=8000)
    APP_DEBUG: bool = Field(default=False)
    APP_CORS_ORIGINS: str = Field(default='*')
    APP_CORS_METHODS: str = Field(default='*')
    APP_USE_HTTPS: bool = Field(default=False)
    GOOGLE_OAUTH_CLIENT_ID: str = Field(default='')
    GOOGLE_OAUTH_CLIENT_SECRET: str = Field(default='')
    GOOGLE_AUTH_URL: str = Field(default='https://accounts.google.com/o/oauth2/auth')
    GOOGLE_TOKEN_URL: str = Field(default='https://oauth2.googleapis.com/token')
    GOOGLE_USERINFO_URL: str = Field(default='https://www.googleapis.com/oauth2/v1/userinfo')
    GOOGLE_OAUTH_SCOPES: list[str] = Field(
        default=[
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.labels',
        ]
    )

    @property
    def get_app_url(self) -> str:
        protocol = 'https' if self.APP_USE_HTTPS else 'http'
        return f'{protocol}://{self.APP_HOST}:{self.APP_PORT}'

    @property
    def get_api_url(self) -> str:
        return f'{self.get_app_url}/api/v1'

    @property
    def get_google_redirect_uri(self) -> str:
        return f'{self.get_app_url}/api/v1/auth/google/callback'


class SMTPSettings(BaseSettings):
    SMTP_HOST: str = Field(default='smtp.gmail.com')
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default='')
    SMTP_PASSWORD: str = Field(default='')


class DatabaseSettings(BaseSettings):
    DB_HOST: str = Field(default='localhost')
    DB_PORT: int = Field(default=5432)
    DB_USER: str = Field(default='user')
    DB_PASSWORD: str = Field(default='password')
    DB_NAME: str = Field(default='dev-db')


class SqliteSettings(DatabaseSettings):
    SQLITE_SYNC_PREFIX: str = 'sqlite://'
    SQLITE_ASYNC_PREFIX: str = 'sqlite+aiosqlite://'

    @property
    def sqlite_sync_uri(self) -> str:
        return f'{self.SQLITE_SYNC_PREFIX}/database.db'

    @property
    def sqlite_async_uri(self) -> str:
        return f'{self.SQLITE_ASYNC_PREFIX}/database.db'

    @property
    def sqlite_sync_uri_memory(self) -> str:
        return f'{self.SQLITE_SYNC_PREFIX}/:memory:'

    @property
    def sqlite_async_uri_memory(self) -> str:
        return f'{self.SQLITE_ASYNC_PREFIX}/:memory:'


class PostgresSettings(DatabaseSettings):
    POSTGRES_SYNC_PREFIX: str = 'postgresql://'
    POSTGRES_ASYNC_PREFIX: str = 'postgresql+asyncpg://'
    DB_USER: str = Field(default='user')
    DB_PASSWORD: str = Field(default='postgres')

    @property
    def postgres_sync_uri(self) -> str:
        return f'{self.POSTGRES_SYNC_PREFIX}{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def postgres_async_uri(self) -> str:
        return f'{self.POSTGRES_ASYNC_PREFIX}' f'{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


class RedisSettings(BaseSettings):
    REDIS_HOST: str = Field(default='localhost')
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    @property
    def redis_uri(self) -> str:
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'


class CryptoSettings(BaseSettings):
    SECRET_KEY: str = Field(default='secret_key')
    ALGORITHM: str = Field(default='HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = Field(default=15)


class TestUserSettings(BaseSettings):
    TEST_USER_EMAIL: str = Field(default='test@example.com')


class UtilsSettings(BaseSettings):
    DIFFERENCE_TIMESTAMP_JST: int = 9 * 60 * 60


class Settings(
    AppSettings,
    SMTPSettings,
    PostgresSettings,
    SqliteSettings,
    RedisSettings,
    CryptoSettings,
    TestUserSettings,
    UtilsSettings,
):
    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
