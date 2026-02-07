"""User model"""

from datetime import datetime
from sqlmodel import SQLModel, Field

from app.utils.time import utc_now


class User(SQLModel, table=True):
    """User model - simple username-based identification."""

    __tablename__ = "users"

    user_id: str = Field(primary_key=True, max_length=50)
    created_at: datetime = Field(default_factory=utc_now)
    session_count: int = Field(default=0)

    def increment_session_count(self) -> None:
        """Increment the session count."""
        self.session_count += 1
