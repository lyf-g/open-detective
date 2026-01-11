from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
from pydantic import BaseModel
from src.backend.services.analytics import detect_anomalies

router = APIRouter()

class AnomalyRequest(BaseModel):
    data: List[Dict[str, Any]]
    threshold: float = 2.0

class ProfileRequest(BaseModel):
    repo: str

@router.post("/analytics/anomalies")
async def check_anomalies(request: AnomalyRequest):
    results = detect_anomalies(request.data, request.threshold)
    return {"anomalies": results, "count": len(results)}

@router.post("/analytics/profile")
async def get_repo_profile(payload: ProfileRequest, request: Request):
    repo = payload.repo
    pool = request.app.state.pool
    
    metrics = {}
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Get latest month data
            await cur.execute("""
                SELECT metric_type, value 
                FROM open_digger_metrics 
                WHERE repo_name = %s 
                AND month = (
                    SELECT MAX(month) FROM open_digger_metrics WHERE repo_name = %s
                )
            """, (repo, repo))
            rows = await cur.fetchall()
            for row in rows:
                metrics[row['metric_type']] = float(row['value'])
    
    if not metrics:
        # Return mock data if repo not found (for demo purposes)
        if "vue" in repo.lower(): return mock_profile("Vue.js", 95, 80, 90, 70, 85)
        if "react" in repo.lower(): return mock_profile("React", 98, 90, 95, 80, 90)
        return mock_profile(repo, 50, 50, 50, 50, 50)

    # Normalization (Simple Heuristic)
    def norm(val, max_val):
        return min(100, max(0, (val / max_val) * 100))

    radar_data = [
        {"name": "Activity", "value": norm(metrics.get('activity', 0), 1000), "max": 100},
        {"name": "Stars (Growth)", "value": norm(metrics.get('stars', 0), 500), "max": 100}, # Monthly growth
        {"name": "OpenRank", "value": norm(metrics.get('openrank', 0), 200), "max": 100},
        {"name": "Bus Factor", "value": norm(metrics.get('bus_factor', 0) * 20, 100), "max": 100}, # BF usually < 5
        {"name": "Velocity", "value": norm(metrics.get('issues_closed', 0), 100), "max": 100},
    ]
    
    return {"repo": repo, "radar": radar_data}

def mock_profile(name, v1, v2, v3, v4, v5):
    return {"repo": name, "radar": [
        {"name": "Activity", "value": v1, "max": 100},
        {"name": "Stars", "value": v2, "max": 100},
        {"name": "OpenRank", "value": v3, "max": 100},
        {"name": "Bus Factor", "value": v4, "max": 100},
        {"name": "Velocity", "value": v5, "max": 100},
    ]}
