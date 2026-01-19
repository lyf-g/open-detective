from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str | None = None


class Session(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime


class Message(BaseModel):
    id: int | None = None
    role: str
    content: str
    evidence_sql: str | None = None
    evidence_data: list[dict] | None = None


class ChatResponse(BaseModel):
    answer: str
    sql_query: str
    data: list[dict[str, Any]]
    engine_source: str


class DossierResponse(BaseModel):
    username: str
    codename: str
    threat_level: str
    psych_profile: str
    skills: list[dict[str, Any]]
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str
    python_version: str | None = None
    environment: str | None = None
    log_level: str | None = None
    db_connected: bool
    redis_connected: bool | None = None
    details: dict[str, Any] | None = None
    timestamp: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    rating: str
    comment: str | None = None
    message_index: int | None = None
