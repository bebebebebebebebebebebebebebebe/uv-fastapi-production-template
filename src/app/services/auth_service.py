import os

from fastapi.security import OAuth2PasswordBearer
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from src.app.core.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY


def create_google_oauth_credentials() -> Credentials:
    creds: Credentials | None = None
    try:
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', settings.GOOGLE_OAUTH_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', settings.GOOGLE_OAUTH_SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                logger.info('Successfully create token.json')
        return creds
    except Exception as e:
        logger.error(f'Error creating Google OAuth credentials: {e}')
        raise e
