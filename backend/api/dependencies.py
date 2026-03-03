from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db
from infrastructure.redis import CacheService, RateLimiter, get_redis_client

# Database session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_cache_service() -> AsyncGenerator[CacheService, None]:
    client = get_redis_client()
    yield CacheService(client)
    await client.aclose()


async def get_rate_limiter() -> AsyncGenerator[RateLimiter, None]:
    client = get_redis_client()
    yield RateLimiter(client)
    await client.aclose()


Cache = Annotated[CacheService, Depends(get_cache_service)]
Limiter = Annotated[RateLimiter, Depends(get_rate_limiter)]
