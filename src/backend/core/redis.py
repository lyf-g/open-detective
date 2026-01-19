import redis.asyncio as redis

from src.backend.core.config import settings
from src.backend.services.logger import logger

try:
    redis_client = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True,
    )
except Exception as e:
    logger.error("redis_init_failed", error=str(e), url=settings.REDIS_URL)
    redis_client = None


async def is_redis_available() -> bool:
    """Check if redis is reachable."""
    if not redis_client:
        return False
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
