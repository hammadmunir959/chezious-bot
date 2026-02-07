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

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def create_session(self, user_id: str) -> ChatSession:
        """
        Create a new chat session for a user.

        Args:
            user_id: The user's ID

        Returns:
            New ChatSession instance
        """
        # Ensure user exists
        await self.user_service.get_or_create_user(user_id)

        # Create session
        chat_session = ChatSession(user_id=user_id)
        self.session.add(chat_session)
        await self.session.flush()

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
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        chat_session = result.scalar_one_or_none()

        if not chat_session:
            raise SessionNotFoundException(str(session_id))

        return chat_session

    async def get_user_sessions(self, user_id: str) -> list[ChatSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: The user's ID

        Returns:
            List of ChatSession instances
        """
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
        )
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
        result = await self.session.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        chat_session = result.scalar_one_or_none()

        if not chat_session:
            raise SessionNotFoundException(str(session_id))

        return chat_session

    async def archive_session(self, session_id: UUID) -> ChatSession:
        """
        Archive a session.

        Args:
            session_id: The session UUID

        Returns:
            Updated ChatSession instance
        """
        chat_session = await self.get_session(session_id)
        chat_session.archive()
        await self.session.flush()

        logger.info(f"Archived session {session_id}")
        return chat_session

    async def increment_message_count(self, session_id: UUID) -> None:
        """Increment the session's message count."""
        chat_session = await self.get_session(session_id)
        chat_session.increment_message_count()
        await self.session.flush()
