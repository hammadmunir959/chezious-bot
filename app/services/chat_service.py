"""Chat service for orchestrating chat interactions"""

from uuid import UUID
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.core.logging import get_logger
from app.services.session_service import SessionService
from app.services.context_service import ContextService
from app.llm.groq_client import groq_client

logger = get_logger(__name__)


class ChatService:
    """Service for chat orchestration."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_service = SessionService(session)
        self.context_service = ContextService(session)

    def validate_message(self, content: str) -> str:
        """
        Validate user message.

        Args:
            content: Message content

        Returns:
            Validated content

        Raises:
            ValidationException: If validation fails
        """
        content = content.strip()

        if not content:
            raise ValidationException("Message cannot be empty")

        if len(content) > settings.max_message_length:
            raise ValidationException(
                f"Message exceeds maximum length of {settings.max_message_length} characters",
                details={
                    "max_length": settings.max_message_length,
                    "provided_length": len(content),
                },
            )

        return content

    async def handle_chat(
        self,
        session_id: UUID,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Handle a chat request with streaming response.

        Args:
            session_id: The session UUID
            user_message: The user's message

        Yields:
            Response tokens as they arrive

        Raises:
            ValidationException: If message validation fails
            SessionNotFoundException: If session doesn't exist
        """
        # 1. Validate input
        user_message = self.validate_message(user_message)
        logger.info(f"Processing chat for session {session_id}")

        # 2. Verify session exists
        chat_session = await self.session_service.get_session(session_id)
        logger.debug(f"Session verified: {chat_session.id}")

        # 3. Save user message
        await self.context_service.save_message(
            session_id, "user", user_message
        )
        await self.session_service.increment_message_count(session_id)

        # 4. Get context messages
        context_messages = await self.context_service.get_context_messages(
            session_id
        )

        # 5. Build LLM messages (without current message since it's in context)
        llm_messages = self.context_service.build_messages_for_llm(
            context_messages[:-1],  # Exclude the just-saved message
            user_message,
        )

        # 6. Stream response from Groq
        full_response: list[str] = []
        async for token in groq_client.stream_chat(llm_messages):
            full_response.append(token)
            yield token

        # 7. Save assistant response
        assistant_content = "".join(full_response)
        await self.context_service.save_message(
            session_id, "assistant", assistant_content
        )
        await self.session_service.increment_message_count(session_id)

        logger.info(
            f"Chat completed for session {session_id}",
            extra={"response_length": len(assistant_content)},
        )

    async def get_response(
        self,
        session_id: UUID,
        user_message: str,
    ) -> str:
        """
        Get a complete (non-streaming) response.

        Args:
            session_id: The session UUID
            user_message: The user's message

        Returns:
            Complete response text
        """
        tokens: list[str] = []
        async for token in self.handle_chat(session_id, user_message):
            tokens.append(token)
        return "".join(tokens)
