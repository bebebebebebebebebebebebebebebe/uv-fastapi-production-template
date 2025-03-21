from src.app.schemas.token_schemas import GoogleOAuthUserPayload
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_google_oauth_payload():
    payload = GoogleOAuthUserPayload(
        sub='1234567890',
        exp=1618449600,
        iat=1618446000,
        iss='https://accounts.google.com',
        aud='1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com',
        azp='1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com',
        email='test@example.com',
        email_verified=True,
        name='John Doe',
        picture='https://lh3.googleusercontent.com/a-/AOh14Gj8901234567890',
    )
    logger.info(f'payload: {payload}')
    assert payload.sub == '1234567890'
    assert payload.exp == 1618449600
