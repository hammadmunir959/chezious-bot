from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Schema for a chat message request."""
    message: str = Field(..., min_length=1, description="The user's message text.")
    user_id: str = Field("guest", description="Unique identifier for the user.")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity.")

class ChatResponse(BaseModel):
    """Schema for the agent's chat response."""
    reply: str
    thread_id: str
