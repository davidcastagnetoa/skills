import uuid
from datetime import datetime, timezone


def generate_session_id() -> uuid.UUID:
    """Generate a new UUID v4 session identifier."""
    return uuid.uuid4()


def utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)
