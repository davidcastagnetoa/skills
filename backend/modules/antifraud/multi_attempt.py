"""Multi-attempt detector.

Detects suspicious patterns of multiple verification attempts from
the same device or IP address within a time window.
"""

import time

import structlog

from modules.antifraud.models import MultiAttemptResult

logger = structlog.get_logger()

_MAX_ATTEMPTS_PER_DEVICE = 3
_MAX_DOCS_PER_IP = 2
_TIME_WINDOW_SECONDS = 3600  # 1 hour


class MultiAttemptDetector:
    """Detect repeated verification attempts."""

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client

    async def check(
        self,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        document_number: str | None = None,
    ) -> MultiAttemptResult:
        """Check for suspicious multi-attempt patterns.

        Tracks:
        - Attempts per device fingerprint (max 3/hour)
        - Different document numbers per IP (max 2/hour)
        """
        attempts_count = 0
        different_docs = 0

        if self._redis is None:
            return MultiAttemptResult()

        now = time.time()

        try:
            # Track attempts by device
            if device_fingerprint:
                device_key = f"attempts:device:{device_fingerprint}"
                attempts_count = await self._increment_counter(device_key, now)

            # Track different documents by IP
            if ip_address and document_number:
                ip_docs_key = f"attempts:ip_docs:{ip_address}"
                different_docs = await self._track_unique_docs(
                    ip_docs_key, document_number, now
                )

        except Exception:
            logger.exception("multi_attempt.redis_error")

        is_suspicious = (
            attempts_count > _MAX_ATTEMPTS_PER_DEVICE
            or different_docs > _MAX_DOCS_PER_IP
        )

        if is_suspicious:
            logger.warning(
                "multi_attempt.suspicious",
                device_fp=device_fingerprint,
                ip=ip_address,
                attempts=attempts_count,
                docs=different_docs,
            )

        return MultiAttemptResult(
            is_suspicious=is_suspicious,
            attempts_count=attempts_count,
            different_documents=different_docs,
            time_window_minutes=_TIME_WINDOW_SECONDS // 60,
        )

    async def _increment_counter(self, key: str, now: float) -> int:
        """Increment a sliding window counter in Redis."""
        pipe = self._redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.zremrangebyscore(key, 0, now - _TIME_WINDOW_SECONDS)
        pipe.zcard(key)
        pipe.expire(key, _TIME_WINDOW_SECONDS)
        results = await pipe.execute()
        return int(results[2])

    async def _track_unique_docs(self, key: str, doc_number: str, now: float) -> int:
        """Track unique document numbers per key in Redis."""
        pipe = self._redis.pipeline()
        pipe.sadd(key, doc_number)
        pipe.scard(key)
        pipe.expire(key, _TIME_WINDOW_SECONDS)
        results = await pipe.execute()
        return int(results[1])
