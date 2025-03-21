from fastapi import FastAPI

from src.app.api import router as api_router
from src.utils.logger import get_logger

logger = get_logger(__name__)
app = FastAPI()

app.include_router(api_router)
