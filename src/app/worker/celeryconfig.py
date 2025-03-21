from src.app.core.config import settings

broker_url = settings.redis_uri
result_backend = settings.redis_uri
broker_connection_retry_on_startup = True
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
