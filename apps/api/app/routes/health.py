from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cache
from app.database import get_session

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(
    session: AsyncSession = Depends(get_session), cache: Redis = Depends(get_cache)
) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        await cache.ping()
    except (RedisError, SQLAlchemyError, OSError) as error:
        raise HTTPException(
            503,
            detail={"code": "dependency_unavailable", "messageKey": "errors.notReady"},
        ) from error
    return {"status": "ready", "database": "ok", "cache": "ok"}
