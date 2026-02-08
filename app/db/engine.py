"""Database engine configuration with resilience."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel

# Resilience fallback for tenacity
try:
    from tenacity import retry, stop_after_attempt, wait_fixed
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    # No-op decorators if tenacity is missing
    def retry(*args, **kwargs):
        return lambda f: f
    def stop_after_attempt(*args, **kwargs):
        return None
    def wait_fixed(*args, **kwargs):
        return None

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

if not HAS_TENACITY:
    logger.warning("Tenacity library not found. Database retries will be disabled.")

# Connection pool settings
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

# Create async engine with pooling and timeout controls
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
)
async def verify_connection() -> None:
    """Attempt to connect to the database."""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

async def init_db() -> None:
    """Initialize database and verify connection."""
    try:
        await verify_connection()
        logger.info("Database connection verified successfully")
    except Exception as e:
        logger.critical(f"DATABASE CONNECTION FAIL: {e}")
        raise RuntimeError(f"Database unavailable: {e}")


async def close_db() -> None:
    """Safe cleanup of database resources."""
    try:
        await engine.dispose()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")
