"""Message model"""

from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.session import ChatSession

from app.utils.time import utc_now

# Use Enum for database compatibility and strict validation
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(SQLModel, table=True):
    """
    Represents a single message within a chat session.
    """

    __tablename__ = "messages"

    id: UUID = Field(
        default_factory=uuid4, 
        primary_key=True,
        description="Unique identifier for the message"
    )
    
    session_id: UUID = Field(
        foreign_key="chat_sessions.id", 
        index=True,
        description="Reference to the parent chat session"
    )
    
    role: MessageRole = Field(
        max_length=10,
        index=True,
        description="The role of the message sender (system, user, or assistant)"
    )
    
    content: str = Field(
        description="The actual text content of the message"
    )
    
    created_at: datetime = Field(
        default_factory=utc_now,
        index=True,
        description="Timestamp when the message was created"
    )
    
    # Relationships
    session: "ChatSession" = Relationship(back_populates="messages")

    @classmethod
    def create_user_message(cls, session_id: UUID, content: str) -> "Message":
        """Factory method to create a user message."""
        return cls(session_id=session_id, role=MessageRole.USER, content=content)

    @classmethod
    def create_assistant_message(cls, session_id: UUID, content: str) -> "Message":
        """Factory method to create an assistant message."""
        return cls(session_id=session_id, role=MessageRole.ASSISTANT, content=content)

    @classmethod
    def create_system_message(cls, session_id: UUID, content: str) -> "Message":
        """Factory method to create a system/prompt message."""
        return cls(session_id=session_id, role=MessageRole.SYSTEM, content=content)
