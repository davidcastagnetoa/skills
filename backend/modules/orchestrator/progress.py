"""Session progress tracker backed by Redis."""

import json
import time
from datetime import datetime, timezone

import structlog

from modules.orchestrator.models import PipelinePhase, SessionProgress

logger = structlog.get_logger()


class ProgressTracker:
    """Tracks pipeline progress for a session in Redis."""

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client

    async def start(self, session_id: str) -> None:
        """Mark session pipeline as started."""
        if self._redis is None:
            return
        progress = SessionProgress(
            session_id=session_id,
            started_at=datetime.now(timezone.utc),
        )
        await self._redis.setex(
            f"progress:{session_id}",
            120,  # TTL 2 minutes
            progress.model_dump_json(),
        )

    async def update(self, session_id: str, phase: PipelinePhase) -> None:
        """Update the current phase for a session."""
        if self._redis is None:
            return
        raw = await self._redis.get(f"progress:{session_id}")
        if not raw:
            return
        data = json.loads(raw)
        data["current_phase"] = phase.value
        started = data.get("started_at")
        if started:
            start_dt = datetime.fromisoformat(started)
            data["elapsed_ms"] = int(
                (datetime.now(timezone.utc) - start_dt).total_seconds() * 1000
            )
        await self._redis.setex(
            f"progress:{session_id}", 120, json.dumps(data, default=str)
        )

    async def complete_phase(self, session_id: str, phase: PipelinePhase) -> None:
        """Mark a phase as completed."""
        if self._redis is None:
            return
        raw = await self._redis.get(f"progress:{session_id}")
        if not raw:
            return
        data = json.loads(raw)
        completed = data.get("phases_completed", [])
        if phase.value not in completed:
            completed.append(phase.value)
        data["phases_completed"] = completed
        data["current_phase"] = None
        started = data.get("started_at")
        if started:
            start_dt = datetime.fromisoformat(started)
            data["elapsed_ms"] = int(
                (datetime.now(timezone.utc) - start_dt).total_seconds() * 1000
            )
        await self._redis.setex(
            f"progress:{session_id}", 120, json.dumps(data, default=str)
        )

    async def get(self, session_id: str) -> SessionProgress | None:
        """Get current progress for a session."""
        if self._redis is None:
            return None
        raw = await self._redis.get(f"progress:{session_id}")
        if not raw:
            return None
        return SessionProgress.model_validate_json(raw)

    async def finish(self, session_id: str) -> None:
        """Remove progress tracking for a completed session."""
        if self._redis is None:
            return
        await self._redis.delete(f"progress:{session_id}")
