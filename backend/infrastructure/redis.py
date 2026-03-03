import json
import time
from typing import Any

import redis.asyncio as redis

from api.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:  # type: ignore[type-arg]
    """Get a Redis async client from the pool."""
    return redis.Redis(connection_pool=redis_pool)


class CacheService:
    """Key-value cache backed by Redis."""

    def __init__(self, client: redis.Redis | None = None) -> None:  # type: ignore[type-arg]
        self._client = client or get_redis_client()

    async def get(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        serialized = json.dumps(value, default=str)
        if ttl:
            await self._client.setex(key, ttl, serialized)
        else:
            await self._client.set(key, serialized)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def health_check(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False


class RateLimiter:
    """Sliding window rate limiter backed by Redis."""

    def __init__(self, client: redis.Redis | None = None) -> None:  # type: ignore[type-arg]
        self._client = client or get_redis_client()

    async def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Return True if the request is allowed, False if rate limited."""
        now = time.time()
        window_start = now - window_seconds
        pipe = self._client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set TTL on the key
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count: int = results[1]

        return current_count < max_requests

    async def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Return the number of remaining requests in the current window."""
        now = time.time()
        window_start = now - window_seconds

        pipe = self._client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()
        current_count: int = results[1]

        return max(0, max_requests - current_count)
