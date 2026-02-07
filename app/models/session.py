"""Chat session model"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Literal
from sqlmodel import SQLModel, Field

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
