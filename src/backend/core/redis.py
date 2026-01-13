import redis.asyncio as redis
from src.backend.core.config import settings
from src.backend.services.logger import logger

try:
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
except Exception as e:
    logger.warning(f"Redis initialization failed: {e}")
    redis_client = None
