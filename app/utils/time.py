"""Time and datetime utilities"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""
    return dt.isoformat()


def timestamp_to_datetime(timestamp: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    return datetime.fromisoformat(timestamp)
