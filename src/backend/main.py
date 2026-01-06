import os
import mysql.connector
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict, Any
from src.backend.services.engine_factory import get_sql_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open MySQL connection with retries
    max_retries = 5
    retry_delay = 5
    
    conn = None
    for i in range(max_retries):
        try:
            print(f"📡 Attempting to connect to MySQL (Attempt {i+1}/{max_retries})...")
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "open_detective")
            )
            if conn.is_connected():
                print("✅ Successfully connected to MySQL.")
                app.state.db = conn
                break
        except Exception as e:
            print(f"⚠️ MySQL not ready yet: {e}")
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("❌ Max retries reached. Backend shutting down.")
                raise e
    
    yield
    # Shutdown: Close DB connection
    if conn and conn.is_connected():
        app.state.db.close()

app = FastAPI(
    title="Open-Detective API",
    description="Backend for Open-Detective",
    version="0.1.0",
    lifespan=lifespan
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sql_query: str
    data: List[Dict[str, Any]]
    engine_source: str

class HealthResponse(BaseModel):
    status: str
    version: str

# Version 1 Router
router_v1 = APIRouter(prefix="/api/v1")

@router_v1.post("/chat", response_model=ChatResponse)
async def chat(request_request: Request, chat_request: ChatRequest):
    print(f"Received message: {chat_request.message}")
    
    # 1. Generate SQL via configured engine
    engine_type_raw = os.getenv("SQL_ENGINE_TYPE", "mock")
    # Clean possible trailing comments/spaces from env
    engine_type = engine_type_raw.split('#')[0].strip().lower()
    
    engine = get_sql_engine()
    sql_query = engine(chat_request.message)
    
    if not sql_query:
        return ChatResponse(
            answer="Sorry, I couldn't understand the repository name. Try asking about 'vue', 'fastapi', or 'react'.",
            sql_query="",
            data=[],
            engine_source=engine_type
        )

    # 2. Execute SQL
    data = []
    try:
        print(f"🚀 Executing SQL: {sql_query}")
        # MySQL dictionary cursor
        cursor = request_request.app.state.db.cursor(dictionary=True)
        cursor.execute(sql_query)
        data = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(f"❌ SQL Execution Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Formulate Answer
    if data:
        if engine_type == "sqlbot":
            print(f"🧠 Asking AI to interpret {len(data)} records...")
            from src.backend.services.sqlbot_client import SQLBotClient
            client = SQLBotClient()
            answer = client.generate_summary(chat_request.message, data)
            print(f"✍️ AI Interpretation: {answer[:50]}...")
        else:
            answer = f"Found {len(data)} records for your query."
    else:
        answer = "No data found correlating to your request."

    return ChatResponse(
        answer=answer,
        sql_query=sql_query,
        data=data,
        engine_source=engine_type
    )

@router_v1.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@router_v1.get("/sqlbot-health")
async def sqlbot_health():
    """Checks if the SQLBot service is reachable."""
    import requests
    endpoint = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
    try:
        # Just a simple ping to the root
        res = requests.get(endpoint, timeout=2)
        return {"status": "reachable", "code": res.status_code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}

# Include Router
app.include_router(router_v1)

@app.get("/")
def read_root():
    return {"message": "Open-Detective Backend is running! Access v1 at /api/v1"}