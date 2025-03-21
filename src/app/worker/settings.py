# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
import celery_aio_pool as aio_pool
from celery import Celery

app = Celery(
    'tasks',
    worker_pool=aio_pool.pool.AsyncIOPool,
)
app.config_from_object('src.app.worker.celeryconfig')
