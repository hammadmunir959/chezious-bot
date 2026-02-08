"""Background cleanup service for expired sessions."""

from datetime import timedelta
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import ChatSession
from app.db.engine import async_session
from app.core.logging import get_logger
from app.utils.time import utc_now

logger = get_logger(__name__)


async def cleanup_expired_sessions() -> int:
    """
    Archive sessions that have been inactive for 7 days.
    
    Returns:
        Number of sessions archived.
    """
    cutoff = utc_now() - timedelta(days=7)
    
    async with async_session() as db:
        try:
            # Update status to 'archived' for active sessions older than cutoff
            result = await db.execute(
                update(ChatSession)
                .where(ChatSession.last_activity_at < cutoff)
                .where(ChatSession.status == "active")
                .values(status="archived")
            )
            await db.commit()
            
            archived_count = result.rowcount
            if archived_count > 0:
                logger.info(f"Archived {archived_count} inactive sessions")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            await db.rollback()
            return 0
