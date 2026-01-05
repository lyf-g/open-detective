import os
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict, Any
from src.backend.services.sql_engine import mock_text_to_sql

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open DB connection
    app.state.db = sqlite3.connect(DB_PATH, check_same_thread=False)
    app.state.db.row_factory = sqlite3.Row
    yield
    # Shutdown: Close DB connection
    app.state.db.close()

app = FastAPI(
    title="Open-Detective API",
    description="Backend for Open-Detective",
    version="0.1.0",
    lifespan=lifespan
)

# Version 1 Router
router_v1 = APIRouter(prefix="/api/v1")

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '../../open_detective.db')

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sql_query: str
    data: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    status: str
    version: str

@router_v1.post("/chat", response_model=ChatResponse)
async def chat(request_request: Request, chat_request: ChatRequest):
    print(f"Received message: {chat_request.message}")
    
    # 1. Generate SQL (Mock AI)
    sql_query = mock_text_to_sql(chat_request.message)
    
    if not sql_query:
        return ChatResponse(
            answer="Sorry, I couldn't understand the repository name. Try asking about 'vue', 'fastapi', or 'react'.",
            sql_query="",
            data=[]
        )

    # 2. Execute SQL
    data = []
    try:
        cursor = request_request.app.state.db.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Formulate Answer
    if data:
        answer = f"Found {len(data)} records for your query."
    else:
        answer = "No data found."

    return ChatResponse(
        answer=answer,
        sql_query=sql_query,
        data=data
    )

@router_v1.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "version": "0.1.0"}

# Include Router
app.include_router(router_v1)

@app.get("/")
def read_root():
    return {"message": "Open-Detective Backend is running! Access v1 at /api/v1"}