from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Session(BaseModel):
    id: str
    title: str
    created_at: datetime

class Message(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    evidence_sql: Optional[str] = None
    evidence_data: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    answer: str
    sql_query: str
    data: List[Dict[str, Any]]
    engine_source: str

class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool

class FeedbackRequest(BaseModel):
    session_id: str
    rating: str
    comment: Optional[str] = None
    message_index: Optional[int] = None
