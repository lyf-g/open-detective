from fastapi import APIRouter, Request
from src.backend.schemas.chat import HealthResponse
import os
import requests

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(request: Request):
    db_status = False
    try:
        db_status = request.app.state.db.is_connected()
    except:
        pass
    return {"status": "ok", "version": "0.1.0", "db_connected": db_status}

@router.get("/sqlbot-health")
async def sqlbot_health():
    endpoint = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
    try:
        res = requests.get(endpoint, timeout=2)
        return {"status": "reachable", "code": res.status_code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}
