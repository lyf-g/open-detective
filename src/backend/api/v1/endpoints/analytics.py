from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from src.backend.services.analytics import detect_anomalies

router = APIRouter()

class AnomalyRequest(BaseModel):
    data: List[Dict[str, Any]]
    threshold: float = 2.0

@router.post("/analytics/anomalies")
async def check_anomalies(request: AnomalyRequest):
    results = detect_anomalies(request.data, request.threshold)
    return {"anomalies": results, "count": len(results)}
