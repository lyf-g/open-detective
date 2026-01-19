from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from src.backend.services.analytics import detect_anomalies

router = APIRouter()


class AnomalyRequest(BaseModel):
    data: list[dict[str, Any]] = Field(..., description="Time-series data records to analyze.")
    threshold: float = Field(2.0, description="Z-score threshold for anomaly detection.")


class ProfileRequest(BaseModel):
    repo: str = Field(..., description="Full repository name (owner/repo).")

    @field_validator("repo")
    @classmethod
    def validate_repo_name(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("Invalid repository format. Expected 'owner/repo'")
        return v


class DossierRequest(BaseModel):
    username: str = Field(..., description="GitHub username to investigate.")


class SentimentRequest(BaseModel):
    repo: str = Field(..., description="Full repository name (owner/repo).")

    @field_validator("repo")
    @classmethod
    def validate_repo_name(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("Invalid repository format. Expected 'owner/repo'")
        return v


@router.post("/analytics/anomalies")
async def check_anomalies(request: AnomalyRequest):
    """Detect statistical anomalies in provided time-series data."""
    results = detect_anomalies(request.data, request.threshold)
    return {"anomalies": results, "count": len(results)}


@router.post("/analytics/dossier")
async def get_suspect_dossier(request: DossierRequest):
    """Generate a psychological and skill profile for a given GitHub contributor."""
    user = request.username
    # Mock Dossier Generation (In real app, query GitHub/OpenDigger user metrics)

    codenames = {
        "antfu": "The Architect",
        "yyx990803": "The Creator",
        "torvalds": "The Kernel",
        "rich-harris": "Speed Demon",
    }

    codename = codenames.get(user.lower(), "Unknown Operative")
    threat = 5 if user.lower() in codenames else 2

    return {
        "username": user,
        "codename": codename,
        "threat_level": f"DEFCON {threat}",
        "psych_profile": "Highly disciplined. Shows signs of sleep deprivation. Obsessed with performance optimization.",
        "skills": [
            {"name": "Coding Speed", "value": 98},
            {"name": "Architecture", "value": 95},
            {"name": "Community", "value": 90},
            {"name": "Debugging", "value": 88},
            {"name": "Innovation", "value": 92},
        ],
        "status": "ACTIVE SURVEILLANCE",
    }


@router.post("/analytics/profile")
async def get_repo_profile(payload: ProfileRequest, request: Request):
    """Retrieve repository metrics and generate a normalized radar chart profile."""
    repo = payload.repo
    pool = request.app.state.pool

    metrics = {}

    async with pool.acquire() as conn, conn.cursor() as cur:
        # Get latest month data
        await cur.execute(
            """
                SELECT metric_type, value 
                FROM open_digger_metrics 
                WHERE repo_name = %s 
                AND month = (
                    SELECT MAX(month) FROM open_digger_metrics WHERE repo_name = %s
                )
            """,
            (repo, repo),
        )
        rows = await cur.fetchall()
        for row in rows:
            metrics[row["metric_type"]] = float(row["value"])

    if not metrics:
        # Return mock data if repo not found (for demo purposes)
        MOCK_DATA_CONFIG = {
            "vue": ("Vue.js", 95, 80, 90, 70, 85),
            "react": ("React", 98, 90, 95, 80, 90),
        }
        for key, params in MOCK_DATA_CONFIG.items():
            if key in repo.lower():
                return mock_profile(*params)
        return mock_profile(repo, 50, 50, 50, 50, 50)

    # Normalization (Simple Heuristic)
    def norm(val, max_val):
        return min(100, max(0, (val / max_val) * 100))

    radar_data = [
        {
            "name": "Activity",
            "value": norm(metrics.get("activity", 0), 1000),
            "max": 100,
        },
        {
            "name": "Stars (Growth)",
            "value": norm(metrics.get("stars", 0), 500),
            "max": 100,
        },  # Monthly growth
        {
            "name": "OpenRank",
            "value": norm(metrics.get("openrank", 0), 200),
            "max": 100,
        },
        {
            "name": "Bus Factor",
            "value": norm(metrics.get("bus_factor", 0) * 20, 100),
            "max": 100,
        },  # BF usually < 5
        {
            "name": "Velocity",
            "value": norm(metrics.get("issues_closed", 0), 100),
            "max": 100,
        },
    ]

    return {"repo": repo, "radar": radar_data}


def mock_profile(name, v1, v2, v3, v4, v5):
    return {
        "repo": name,
        "radar": [
            {"name": "Activity", "value": v1, "max": 100},
            {"name": "Stars", "value": v2, "max": 100},
            {"name": "OpenRank", "value": v3, "max": 100},
            {"name": "Bus Factor", "value": v4, "max": 100},
            {"name": "Velocity", "value": v5, "max": 100},
        ],
    }


@router.post("/analytics/sentiment")
async def get_sentiment(payload: SentimentRequest):
    """Analyze community sentiment for a repository based on keywords and scores."""
    repo = payload.repo.lower()

    # Mock Data
    score = 0.85
    keywords = [
        {"name": "Performance", "value": 100},
        {"name": "Easy", "value": 95},
        {"name": "Docs", "value": 90},
        {"name": "Community", "value": 85},
        {"name": "Flexible", "value": 80},
        {"name": "Lightweight", "value": 75},
        {"name": "Buggy", "value": 30},
        {"name": "Breaking Changes", "value": 25},
        {"name": "Complex", "value": 20},
    ]

    if "react" in repo:
        score = 0.75
        keywords = [
            {"name": "Hooks", "value": 100},
            {"name": "Ecosystem", "value": 95},
            {"name": "Jobs", "value": 90},
            {"name": "Rerender", "value": 60},
            {"name": "Complexity", "value": 50},
        ]
    elif "angular" in repo:
        score = 0.65
        keywords = [
            {"name": "Robust", "value": 100},
            {"name": "Enterprise", "value": 95},
            {"name": "CLI", "value": 90},
            {"name": "Boilerplate", "value": 70},
            {"name": "Learning Curve", "value": 80},
        ]

    return {"repo": repo, "score": score, "keywords": keywords}