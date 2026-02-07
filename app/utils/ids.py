"""UUID generation utilities"""

import uuid


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4."""
    return uuid.uuid4()


def generate_request_id() -> str:
    """Generate a short request ID for logging."""
    return uuid.uuid4().hex[:12]
