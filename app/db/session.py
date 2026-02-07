"""Database session dependency"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session injection."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
