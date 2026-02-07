"""Session-related schemas"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request to create a new session."""

    user_id: str = Field(..., min_length=1, max_length=50)


class SessionResponse(BaseModel):
    """Response for session operations."""

    id: UUID
    user_id: str
    created_at: datetime
    status: str
    message_count: int


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionResponse]
