"""Rate limiting middleware using SlowAPI"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_string() -> str:
    """Get rate limit string for decorators."""
    return f"{settings.rate_limit_per_minute}/minute"
