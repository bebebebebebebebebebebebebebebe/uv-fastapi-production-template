# src/app/worker/listen.py の修正版
from src.app.core.config import settings
from src.app.worker import tasks

to_email = settings.TEST_USER_EMAIL
subject = 'Test email from celery'
body = 'This is a test email from celery'
result = tasks.send_email_async.delay(to_email, subject, body)
print('done...')
print(result)
