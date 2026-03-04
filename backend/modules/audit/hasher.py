"""Session integrity hasher using HMAC-SHA256.

Computes a rolling hash over all audit events in a session
to ensure the trail has not been tampered with.
"""

import hashlib
import hmac
import json
from datetime import datetime

import structlog

logger = structlog.get_logger()

# Default HMAC key — in production, load from environment/vault
_DEFAULT_KEY = b"verifid-audit-hmac-key-change-in-production"


class SessionHasher:
    """Compute HMAC-SHA256 integrity hashes for audit trails."""

    def __init__(self, secret_key: bytes | None = None) -> None:
        self._key = secret_key or _DEFAULT_KEY

    def hash_event(self, event_data: dict) -> str:
        """Compute HMAC-SHA256 for a single event."""
        serialized = json.dumps(event_data, sort_keys=True, default=str)
        return hmac.new(self._key, serialized.encode(), hashlib.sha256).hexdigest()

    def hash_trail(self, events: list[dict]) -> str:
        """Compute a rolling HMAC-SHA256 over all events in a session.

        Each event's hash includes the previous hash, creating a chain.
        """
        current_hash = ""
        for event in events:
            payload = json.dumps(event, sort_keys=True, default=str)
            data = f"{current_hash}:{payload}".encode()
            current_hash = hmac.new(self._key, data, hashlib.sha256).hexdigest()
        return current_hash

    def verify_trail(self, events: list[dict], expected_hash: str) -> bool:
        """Verify the integrity of an audit trail."""
        computed = self.hash_trail(events)
        return hmac.compare_digest(computed, expected_hash)
