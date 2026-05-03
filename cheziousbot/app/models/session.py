from sqlmodel import SQLModel, Relationship, Field
import uuid
from typing import List, Literal, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .user import User

class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    user: "User" = Relationship(
        back_populates="sessions"
    )
    
    messages: List["ChatMessage"] = Relationship(
        back_populates="session",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "ChatMessage.created_at"}
    )

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(..., foreign_key="sessions.id", index=True)
    
    role: str = Field(...)
    content: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    session: "Session" = Relationship(
        back_populates="messages"
    )
