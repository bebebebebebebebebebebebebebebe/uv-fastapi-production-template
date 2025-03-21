from fastapi import APIRouter

from src.app.api.v1.auth.router import router as auth_router
from src.app.api.v1.health_check.router import router as health_check_router
from src.app.api.v1.users.router import router as users_router

router = APIRouter(prefix='/v1')
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(health_check_router)
