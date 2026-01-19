import os
import sys
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Request

from src.backend.core.config import settings
from src.backend.schemas.chat import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    response_description="Returns the system health status, database connectivity, and environment info.",
    tags=["System"],
)
async def health_check(request: Request):
    db_status = False
    pool_info = {}
    try:
        if hasattr(request.app.state, "pool"):
            pool = request.app.state.pool
            async with pool.acquire() as conn:
                await conn.ping()
                db_status = True
            pool_info = {"size": pool.size, "free": pool.freesize}
    except Exception as e:
        pool_info["error"] = str(e)

    # Redis Check
    redis_status = None
    try:
        from src.backend.core.redis import is_redis_available
        redis_status = await is_redis_available()
    except (ImportError, Exception):
        redis_status = False

    return {
        "status": "ok",
        "version": "1.1.0",
        "python_version": sys.version.split()[0],
        "environment": settings.APP_ENV,
        "log_level": settings.LOG_LEVEL,
        "db_connected": db_status,
        "redis_connected": redis_status,
        "details": pool_info,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ping", tags=["System"], response_model=str)
async def ping():
    """Minimal connectivity check."""
    return "pong"


@router.get("/sqlbot-health", tags=["System"])
async def sqlbot_health():
    endpoint = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(endpoint, timeout=2.0)
            return {"status": "reachable", "code": res.status_code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}
