from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.config import get_settings


async def get_cache() -> AsyncIterator[Redis]:
    cache = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        yield cache
    finally:
        await cache.aclose()
