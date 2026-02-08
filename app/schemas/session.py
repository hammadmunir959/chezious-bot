"""Session-related schemas"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request to create a new session."""

    user_id: str = Field(..., min_length=1, max_length=50)
    name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)


class SessionResponse(BaseModel):
    """Response for session operations."""

    id: UUID
    user_id: str
    created_at: datetime
    status: str
    message_count: int
    user_name: str | None = None
    location: str | None = None


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionResponse]
