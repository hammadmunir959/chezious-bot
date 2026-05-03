from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=120,
        description="Full name of the user."
    )
    phone: str = Field(
        ...,
        description="Phone number in format +92XXXXXXXXXX or 03XXXXXXXXX."
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[A-Za-z'-]+(?:\s[A-Za-z'-]+)*$", v):
            raise ValueError("Name contains invalid characters.")
        return v

    @field_validator("phone")
    def validate_and_normalize_phone(cls, v):
        if not re.match(r"^(?:\+92\d{10}|03\d{9})$", v):
            raise ValueError("Invalid phone number format.")
        
        # Normalization: Convert 03XXXXXXXXX to +923XXXXXXXXX
        if v.startswith("03"):
            v = "+92" + v[1:]
            
        return v

class UserResponse(BaseModel):
    """Schema for user response data."""
    id: str
    name: str
    phone: str
    created_at: datetime
