"""API v1 router"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.chat import router as chat_router

router = APIRouter(prefix="/api/v1")

router.include_router(health_router, tags=["Health"])
router.include_router(users_router, tags=["Users"])
router.include_router(sessions_router, tags=["Sessions"])
router.include_router(chat_router, tags=["Chat"])
