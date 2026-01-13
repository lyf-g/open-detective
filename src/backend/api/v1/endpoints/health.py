from fastapi import APIRouter, Request
from src.backend.schemas.chat import HealthResponse
import os
import requests

router = APIRouter()

from datetime import datetime, timezone

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    db_status = False
    pool_info = {}
    try:
        if hasattr(request.app.state, 'pool'):
            pool = request.app.state.pool
            async with pool.acquire() as conn:
                await conn.ping()
                db_status = True
            pool_info = {
                "size": pool.size,
                "free": pool.freesize
            }
    except Exception as e:
        pool_info["error"] = str(e)
    
    return {
        "status": "ok", 
        "version": "1.0.0", 
        "db_connected": db_status,
        "details": pool_info,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/sqlbot-health")
async def sqlbot_health():
    endpoint = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
    try:
        res = requests.get(endpoint, timeout=2)
        return {"status": "reachable", "code": res.status_code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}