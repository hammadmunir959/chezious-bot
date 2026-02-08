"""Context service for managing conversation context"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import Message
from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.core.logging import get_logger
from app.llm.prompts import get_system_prompt

logger = get_logger(__name__)


class ContextService:
    """Service for managing conversation context."""

    def __init__(
        self,
        session: AsyncSession,
        max_messages: int | None = None,
    ):
        self.session = session
        self.max_messages = max_messages or settings.context_window_size

    async def get_context_messages(self, session_id: UUID) -> list[Message]:
        """
        Get the last N messages for context.

        Args:
            session_id: The session UUID

        Returns:
            List of Message instances (chronological order)

        Raises:
            DatabaseException: If database query fails
        """
        try:
            result = await self.session.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(self.max_messages)
            )
            messages = list(result.scalars().all())

            # Reverse to chronological order
            messages.reverse()

            logger.debug(
                f"Retrieved {len(messages)} context messages for session {session_id}"
            )
            return messages
        except Exception as e:
            logger.error(f"Failed to get context messages: {e}")
            raise DatabaseException(f"Failed to retrieve messages: {e}")

    def build_messages_for_llm(
        self,
        context_messages: list[Message],
        current_message: str,
        user_name: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, str]]:
        """
        Build the messages list for LLM API call.

        Args:
            context_messages: Previous messages for context
            current_message: The current user message
            user_name: The user's name for personalization
            location: The user's location for branch suggestions

        Returns:
            List of message dicts for Groq API
        """
        llm_messages: list[dict[str, str]] = [
            {"role": "system", "content": get_system_prompt(user_name, location)}
        ]

        # Add context messages
        for msg in context_messages:
            llm_messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Add current message
        llm_messages.append({
            "role": "user",
            "content": current_message,
        })

        total_messages = len(llm_messages)
        logger.debug(f"Built {total_messages} messages for LLM")

        return llm_messages

    async def save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """
        Save a message to the database.

        Args:
            session_id: The session UUID
            role: 'user' or 'assistant'
            content: Message content

        Returns:
            Created Message instance

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            if role == "user":
                message = Message.create_user_message(session_id, content)
            else:
                message = Message.create_assistant_message(session_id, content)

            self.session.add(message)
            await self.session.flush()

            logger.debug(f"Saved {role} message for session {session_id}")
            return message
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise DatabaseException(f"Failed to save message: {e}")

    async def get_session_messages(self, session_id: UUID) -> list[Message]:
        """
        Get all messages for a session.

        Args:
            session_id: The session UUID

        Returns:
            List of Message instances (chronological order)
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
