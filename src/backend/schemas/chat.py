from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    engine: str


class DossierResponse(BaseModel):
    username: str
    codename: str
    threat_level: str
    psych_profile: str
    skills: list[dict[str, Any]]
    status: str = Field(..., description="The overall health status of the system (e.g., ok, error).")


class HealthResponse(BaseModel):
    status: str = Field(..., description="The overall health status of the system (e.g., ok, error).")
    version: str = Field(..., description="System version.")
    python_version: str | None = Field(default=None, description="Running Python version.")
    environment: str | None = Field(default=None, description="App runtime environment.")
    log_level: str | None = Field(default=None, description="Configured logging level.")
    db_connected: bool = Field(..., description="Database connection status.")
    redis_connected: bool | None = Field(default=None, description="Redis connection status.")
    details: dict[str, Any] | None = Field(default=None, description="Detailed status of individual components like database and pool size.")
    timestamp: str | None = Field(default=None, description="ISO timestamp of the health check.")


class FeedbackRequest(BaseModel):
    session_id: str
    rating: str
    comment: str | None = None
    message_index: int | None = None
