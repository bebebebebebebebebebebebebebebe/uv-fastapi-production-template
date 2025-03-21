import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

from src.app.core.config import settings
from src.utils.logger import get_logger

from ..services.auth_service import create_google_oauth_credentials

logger = get_logger(__name__)


def load_jinja_template(template_name: str, **kwargs) -> str:
    env = Environment(loader=FileSystemLoader('src/app/core/templates'))
    template = env.get_template(template_name)
    return template.render(**kwargs)


def send_email_with_gmail(to_email: str, subject: str, body: str) -> bool:
    pass


def send_verify_email_with_gmail(to_email: str, link: str) -> bool:
    creds = create_google_oauth_credentials()
    email_body = 'Please click the link below to verify your email address'
    subject = 'Verify your email address'

    try:
        service = build('gmail', 'v1', credentials=creds)
        html_body = load_jinja_template('verify_email_template.html', subject=subject, link=link, body=email_body)
        message = MIMEText(html_body, 'html')
        message['Subject'] = subject
        message['To'] = to_email
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        logger.info(f'Sending email to {to_email}')
        logger.info(f'Email message: {message}')
        send_result = service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        logger.info(f'Email sent successfully: {send_result}')
        return send_result
    except Exception as e:
        logger.error(f'Error sending email with Gmail API: {e}')
        raise e


if __name__ == '__main__':
    to_email = settings.TEST_USER_EMAIL
    link = 'https://www.google.com'
    send_verify_email_with_gmail(to_email, link)
