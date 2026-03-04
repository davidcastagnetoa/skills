"""Audit service — manages audit trails for verification sessions."""

import json
from datetime import datetime, timezone

import structlog

from modules.audit.anonymizer import anonymize_data
from modules.audit.hasher import SessionHasher
from modules.audit.models import AuditEvent, AuditEventType, AuditTrail

logger = structlog.get_logger()


class AuditService:
    """Manages audit event logging, anonymization, and integrity hashing.

    All events are:
    1. Anonymized (PII masked)
    2. Logged via structlog (JSON format)
    3. Stored in PostgreSQL audit_logs table
    4. Integrity-hashed per session
    """

    def __init__(self, db_session=None, secret_key: bytes | None = None) -> None:
        self._db = db_session
        self._hasher = SessionHasher(secret_key)
        self._session_events: dict[str, list[dict]] = {}

    async def log_event(
        self,
        session_id: str,
        event_type: AuditEventType,
        data: dict | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Log an audit event.

        Args:
            session_id: Verification session ID.
            event_type: Type of event.
            data: Event payload (will be anonymized).
            trace_id: Distributed trace ID for correlation.
        """
        raw_data = data or {}

        # Anonymize PII
        anonymized = anonymize_data(raw_data)

        event = AuditEvent(
            session_id=session_id,
            trace_id=trace_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            data=anonymized,
            anonymized=True,
        )

        # Track events for integrity hash
        event_dict = event.model_dump(mode="json")
        if session_id not in self._session_events:
            self._session_events[session_id] = []
        self._session_events[session_id].append(event_dict)

        # Log via structlog
        logger.info(
            f"audit.{event_type.value}",
            session_id=session_id,
            trace_id=trace_id,
            data=anonymized,
        )

        # Persist to database
        await self._persist_event(event)

    async def log_session_complete(
        self,
        session_id: str,
        decision_status: str,
        confidence_score: float,
    ) -> str:
        """Log session completion and compute integrity hash.

        Returns:
            Integrity hash for the session trail.
        """
        await self.log_event(
            session_id,
            AuditEventType.SESSION_COMPLETED,
            {
                "status": decision_status,
                "confidence_score": confidence_score,
            },
        )

        # Compute integrity hash
        events = self._session_events.get(session_id, [])
        integrity_hash = self._hasher.hash_trail(events)

        # Store hash
        await self._persist_hash(session_id, integrity_hash)

        logger.info(
            "audit.session_hash_computed",
            session_id=session_id,
            n_events=len(events),
            hash=integrity_hash[:16] + "...",
        )

        return integrity_hash

    async def log_error(
        self,
        session_id: str,
        error: Exception,
        trace_id: str | None = None,
    ) -> None:
        """Log a session error."""
        await self.log_event(
            session_id,
            AuditEventType.SESSION_ERROR,
            {"error_type": type(error).__name__, "error_message": str(error)},
            trace_id,
        )

    def verify_trail(self, session_id: str, expected_hash: str) -> bool:
        """Verify the integrity of a session's audit trail."""
        events = self._session_events.get(session_id, [])
        return self._hasher.verify_trail(events, expected_hash)

    async def _persist_event(self, event: AuditEvent) -> None:
        """Write audit event to PostgreSQL."""
        if self._db is None:
            return

        try:
            from sqlalchemy import text

            await self._db.execute(
                text(
                    "INSERT INTO audit_logs (session_id, event_type, event_data, created_at) "
                    "VALUES (:sid, :etype, :edata, :ts)"
                ),
                {
                    "sid": event.session_id,
                    "etype": event.event_type.value,
                    "edata": json.dumps(event.data),
                    "ts": event.timestamp,
                },
            )
            await self._db.commit()
        except Exception:
            logger.exception("audit.persist_failed")

    async def _persist_hash(self, session_id: str, integrity_hash: str) -> None:
        """Store the session integrity hash."""
        if self._db is None:
            return

        try:
            from sqlalchemy import text

            await self._db.execute(
                text(
                    "UPDATE audit_logs SET event_data = event_data || :hash_data "
                    "WHERE session_id = :sid AND event_type = 'session_completed'"
                ),
                {
                    "sid": session_id,
                    "hash_data": json.dumps({"integrity_hash": integrity_hash}),
                },
            )
            await self._db.commit()
        except Exception:
            logger.exception("audit.persist_hash_failed")
