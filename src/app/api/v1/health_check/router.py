from fastapi import APIRouter, Request

from src.utils.logger import get_logger

from .schemas import HealthCheckResponse

router = APIRouter(prefix='/health-check', tags=['health-check'])

logger = get_logger(__name__)


@router.get('', response_model=HealthCheckResponse)
async def health_check(request: Request):
    logger.info('Health check request: %s', request)
    return HealthCheckResponse(
        message='OK',
        status=200,
    )
