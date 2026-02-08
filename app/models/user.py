"""User model"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.session import ChatSession

from app.utils.time import utc_now


class User(SQLModel, table=True):
    """User model - simple username-based identification."""

    __tablename__ = "users"

    user_id: str = Field(primary_key=True, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now)
    session_count: int = Field(default=0)
    
    # Relationships
    sessions: list["ChatSession"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def increment_session_count(self) -> None:
        """Increment the session count."""
        self.session_count += 1
