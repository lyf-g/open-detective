from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from src.backend.services.analytics import detect_anomalies

router = APIRouter()


class AnomalyRequest(BaseModel):
    data: list[dict[str, Any]]
    threshold: float = 2.0


class ProfileRequest(BaseModel):
    repo: str

    @field_validator("repo")
    @classmethod
    def validate_repo_name(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("Invalid repository format. Expected 'owner/repo'")
        return v


class DossierRequest(BaseModel):
    username: str


class SentimentRequest(BaseModel):
    repo: str

    @field_validator("repo")
    @classmethod
    def validate_repo_name(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("Invalid repository format. Expected 'owner/repo'")
        return v



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
