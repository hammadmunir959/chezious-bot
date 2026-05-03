from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from app.db.database import get_db, init_db
from app.core.logging import setup_logging
import logging
from app.core.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import (
    sqlalchemy_exception_handler,
    general_exception_handler,
    validation_exception_handler
)

from app.api.v1.router import api_router
from app.core.config import settings
from app.agent.graph import checkpointer

setup_logging(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()
    
    # Setup Redis checkpointer indices
    try:
        await checkpointer.asetup()
    except Exception as e:
        logger.error(f"Failed to setup Redis checkpointer: {e}")
        
    yield

app = FastAPI(
    title="CheziousBot API",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
