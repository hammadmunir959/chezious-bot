"""User model"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.session import ChatSession

from app.utils.time import utc_now


class User(SQLModel, table=True):
    """
    Represents a user in the system.
    
    Users are identified by a unique user_id (usually provided by the frontend).
    Tracks basic profile info and session statistics.
    """

    __tablename__ = "users"

    user_id: str = Field(
        primary_key=True, 
        max_length=50,
        description="The primary unique identifier for the user"
    )
    
    name: str | None = Field(
        default=None, 
        max_length=100,
        index=True,
        description="Optional display name or username"
    )
    
    city: str | None = Field(
        default=None, 
        max_length=100,
        description="The user's preferred city or current location"
    )
    
    session_count: int = Field(
        default=0,
        description="Total number of chat sessions created by this user"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=utc_now,
        index=True,
        description="Timestamp when the user first interacted with the system"
    )
    
    updated_at: datetime = Field(
        default_factory=utc_now,
        index=True,
        description="Timestamp of the last profile update"
    )
    
    # Relationships
    sessions: list["ChatSession"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def increment_session_count(self) -> None:
        """Atomic-style increment for session tracking."""
        self.session_count += 1
        self.updated_at = utc_now()
