import httpx
import pytest
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    response = await client.get('/api/v1/health-check')
    result = response.json()
    logger.info('Test health check response: %s', result)
    assert response.status_code == 200
    assert result == {'message': 'OK', 'status': 200}
