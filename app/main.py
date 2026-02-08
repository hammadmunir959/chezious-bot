"""CheziousBot - FastAPI Application Entry Point"""

import logging
import sys
from contextlib import asynccontextmanager

# 1. Initialize Logging FIRST (before any other app imports)
# This ensures that even import errors in other modules are logged properly if possible.
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import __version__
from app.core.exceptions import ChatBotException
from app.core.rate_limiter import limiter
from app.db.engine import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical(f"DATABASE STARTUP FAILED: {e}", exc_info=True)
        # We don't raise here if we want the app to stay alive (e.g. to serve a health check)
        # but for a chatbot, DB is critical.
    
    yield

    # Shutdown
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered chatbot for Cheezious pizza brand",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Add Safety Middleware
from app.core.middleware import RequestLoggingMiddleware, ResilienceMiddleware

app.add_middleware(CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ResilienceMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# 3. SAFE ROUTER LOADING
# We wrap this to ensure that if a module has an import error, the server can still boot.
try:
    from app.api import v1_router
    app.include_router(v1_router)
    logger.info("API routers loaded successfully")
except ImportError as e:
    logger.critical(f"CRITICAL IMPORT ERROR IN API LAYER: {e}", exc_info=True)
except Exception as e:
    logger.critical(f"UNEXPECTED ERROR DURING ROUTER INITIALIZATION: {e}", exc_info=True)


# Exception handlers
@app.exception_handler(ChatBotException)
async def chatbot_exception_handler(request: Request, exc: ChatBotException) -> JSONResponse:
    status_map = {
        "SESSION_NOT_FOUND": 404,
        "USER_NOT_FOUND": 404,
        "USER_ALREADY_EXISTS": 409,
        "VALIDATION_ERROR": 400,
        "RATE_LIMIT_EXCEEDED": 429,
        "DATABASE_ERROR": 503,
        "GROQ_API_ERROR": 503,
        "SERVICE_UNAVAILABLE": 503,
        "CONFIGURATION_ERROR": 500,
    }
    status_code = status_map.get(exc.code, 400)
    logger.warning(f"ChatBotException: {exc.code} - {exc.message}")
    return JSONResponse(status_code=status_code, content=exc.to_dict())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": exc.detail}}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)

