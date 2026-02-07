"""Message model"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Literal
from sqlmodel import SQLModel, Field

from app.utils.time import utc_now


MessageRole = Literal["user", "assistant"]


class Message(SQLModel, table=True):
    """Chat message model."""

    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)
    role: str = Field(max_length=10)  # user | assistant
    content: str = Field()
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def create_user_message(cls, session_id: UUID, content: str) -> "Message":
        """Create a user message."""
        return cls(session_id=session_id, role="user", content=content)

    @classmethod
    def create_assistant_message(cls, session_id: UUID, content: str) -> "Message":
        """Create an assistant message."""
        return cls(session_id=session_id, role="assistant", content=content)
