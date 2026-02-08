"""Chat session model"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Literal, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message

from app.utils.time import utc_now


SessionStatus = Literal["active", "archived"]


class ChatSession(SQLModel, table=True):
    """Chat session model."""

    __tablename__ = "chat_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    status: str = Field(default="active")  # active | archived
    message_count: int = Field(default=0)
    
    # Context fields (captured at session creation)
    user_name: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=100)
    
    # Relationships
    user: "User" = Relationship(back_populates="sessions")
    messages: list["Message"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def increment_message_count(self) -> None:
        """Increment the message count."""
        self.message_count += 1

    def archive(self) -> None:
        """Archive the session."""
        self.status = "archived"

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == "active"
