import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Relationship, Field

if TYPE_CHECKING:
    from .order import Order
    from .session import Session

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    name: str = Field(
        default="Guest", 
        min_length=2, 
        max_length=120
    )
    
    phone: str = Field(
        ...,
        max_length=13,
        unique=True
    )
    
    channel: str = Field(default="web")
    preferred_language: str = Field(default="en")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    orders: List["Order"] = Relationship(back_populates="user")
    sessions: List["Session"] = Relationship(
        back_populates="user",
        cascade_delete=True
    )
