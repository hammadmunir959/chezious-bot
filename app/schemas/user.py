"""User-related schemas"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class UserSessionSummary(BaseModel):
    """Summary of a user's session."""

    id: UUID
    created_at: datetime
    status: str
    message_count: int


class UserSessionsResponse(BaseModel):
    """Response for getting user sessions."""

    user_id: str
    sessions: list[UserSessionSummary]
