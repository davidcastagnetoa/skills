"""Document blacklist checker.

Checks if a document number appears in the blacklisted_documents table.
Results are cached in Redis (TTL 5 min) to reduce DB load.
"""

import structlog

from modules.antifraud.models import BlacklistCheckResult

logger = structlog.get_logger()

_CACHE_TTL_SECONDS = 300  # 5 minutes


class BlacklistChecker:
    """Check documents against the blacklist database."""

    def __init__(self, redis_client=None, db_session=None) -> None:
        self._redis = redis_client
        self._db = db_session

    async def check(self, document_number: str | None) -> BlacklistCheckResult:
        """Check if a document is blacklisted.

        Uses Redis cache first, falls back to PostgreSQL.
        """
        if not document_number:
            return BlacklistCheckResult()

        normalized = document_number.upper().replace(" ", "").replace("-", "")
        cache_key = f"blacklist:{normalized}"

        # Check Redis cache
        if self._redis is not None:
            try:
                cached = await self._redis.get(cache_key)
                if cached is not None:
                    is_bl = cached == "1"
                    return BlacklistCheckResult(
                        is_blacklisted=is_bl,
                        reason="document_in_blacklist" if is_bl else None,
                    )
            except Exception:
                logger.warning("blacklist.cache_error")

        # Check database
        is_blacklisted = await self._check_db(normalized)

        # Cache result
        if self._redis is not None:
            try:
                await self._redis.set(
                    cache_key, "1" if is_blacklisted else "0", ex=_CACHE_TTL_SECONDS
                )
            except Exception:
                pass

        return BlacklistCheckResult(
            is_blacklisted=is_blacklisted,
            reason="document_in_blacklist" if is_blacklisted else None,
        )

    async def _check_db(self, document_number: str) -> bool:
        """Query the blacklisted_documents table."""
        if self._db is None:
            return False

        try:
            from sqlalchemy import select, text

            result = await self._db.execute(
                text(
                    "SELECT 1 FROM blacklisted_documents WHERE document_number = :doc_num AND is_active = true LIMIT 1"
                ),
                {"doc_num": document_number},
            )
            return result.scalar() is not None
        except Exception:
            logger.exception("blacklist.db_query_failed")
            return False
