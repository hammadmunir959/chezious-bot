"""Session service for managing chat sessions"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import ChatSession
from app.models.user import User
from app.core.exceptions import SessionNotFoundException
from app.core.logging import get_logger
from app.services.user_service import UserService

logger = get_logger(__name__)


class SessionService:
    """Service for session-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def create_session(
        self, 
        user_id: str, 
        persist: bool = True,
        user_name: str | None = None,
        location: str | None = None,
    ) -> ChatSession:
        """
        Create a new chat session for a user.

        Args:
            user_id: The user's ID
            persist: Whether to save to database immediately
            user_name: Optional user name to store with session
            location: Optional location context for the session

        Returns:
            New ChatSession instance
        """
        # Ensure user exists (only if persisting)
        check_user = persist 
        
        if check_user:
            await self.user_service.get_or_create_user(user_id)

        # Create session with context
        chat_session = ChatSession(
            user_id=user_id,
            user_name=user_name,
            location=location,
        )
        
        if persist:
            self.db.add(chat_session)
            await self.db.flush()
            
            # Increment user's session count
            await self.user_service.increment_session_count(user_id)
            logger.info(f"Created session {chat_session.id} for user {user_id}")
        else:
            logger.info(f"Generated lazy session {chat_session.id} for user {user_id}")
            
        return chat_session

    async def create_session_with_id(
        self, 
        session_id: UUID, 
        user_id: str,
        user_name: str | None = None,
        location: str | None = None,
    ) -> ChatSession:
        """
        Create a session with a specific ID (used for lazy creation).

        Args:
            session_id: The session UUID
            user_id: The user's ID
            user_name: Optional user name to store with session
            location: Optional location context for the session

        Returns:
            ChatSession instance
        """
        # Ensure user exists and get their info
        user = await self.user_service.get_or_create_user(user_id)

        # Use provided values or fall back to user's stored info
        session_user_name = user_name or user.name
        session_location = location or user.city

        # Create session with context
        chat_session = ChatSession(
            id=session_id, 
            user_id=user_id,
            user_name=session_user_name,
            location=session_location,
        )
        self.db.add(chat_session)
        await self.db.flush()

        # Increment user's session count
        await self.user_service.increment_session_count(user_id)

        logger.info(f"Created session {chat_session.id} for user {user_id}")
        return chat_session

    async def get_session(self, session_id: UUID) -> ChatSession:
        """
        Get a session by ID.

        Args:
            session_id: The session UUID

        Returns:
            ChatSession instance

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        chat_session = result.scalar_one_or_none()

        if not chat_session:
            raise SessionNotFoundException(str(session_id))

        return chat_session

    async def get_user_sessions(
        self, 
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        min_messages: int = 0
    ) -> list[ChatSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            min_messages: Minimum message count to include

        Returns:
            List of ChatSession instances
        """
        stmt = (
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.status == "active",
                ChatSession.message_count >= min_messages
            )
            .order_by(ChatSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_session(
        self, user_id: str, session_id: UUID
    ) -> ChatSession:
        """
        Get a specific session for a user.

        Args:
            user_id: The user's ID
            session_id: The session UUID

        Returns:
            ChatSession instance

        Raises:
            SessionNotFoundException: If session doesn't exist or doesn't belong to user
        """
        result = await self.db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()

        if not chat_session:
            raise SessionNotFoundException(str(session_id))

        return chat_session

    async def delete_session(self, session_id: UUID) -> None:
        """
        Delete a session including its messages (via cascade).

        Args:
            session_id: The session UUID

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        chat_session = await self.get_session(session_id)
        await self.db.delete(chat_session)
        await self.db.flush()

        logger.info(f"Deleted session {session_id}")

    async def increment_message_count(self, session_id: UUID) -> None:
        """Increment the session's message count."""
        chat_session = await self.get_session(session_id)
        chat_session.increment_message_count()
        await self.db.flush()
