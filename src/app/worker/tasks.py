import random
import time

import celery

from src.app.core.send_email import send_verify_email_with_gmail
from src.utils.logger import get_logger

from .settings import app

logger = get_logger(__name__)


@app.task
def send_verify_email(to_email: str, link: str):
    response = send_verify_email_with_gmail(to_email, link)
    logger.info(f'Done sending email to {to_email}')
    if not response:
        logger.error(f'Failed to send email to {to_email}')
        return None
    return response


@app.task
def build_server():
    logger.info('Start build server wait 10 sec')
    time.sleep(10)
    server_id = random.randint(1, 1000)
    return server_id


@app.task
def build_servers():
    g = celery.group(build_server.s() for _ in range(4))
    return g()


@app.task
def callback(result):
    for server_id in result:
        logger.info(f'server_id: {server_id}')
    logger.info('clean up')
    return 'Finish build servers'


@app.task
def build_servers_with_cleanup():
    c = celery.chord((build_server.s() for _ in range(4)), callback.s())
    return c()
