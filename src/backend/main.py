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

def detect_anomalies(data: list) -> list:
    """Scans data for significant spikes or drops."""
    if len(data) < 3: return []
    anomalies = []
    # Simple logic: Compare current value to previous month
    for i in range(1, len(data)):
        prev = data[i-1].get('value', 0)
        curr = data[i].get('value', 0)
        if prev == 0: continue
        
        change = (curr - prev) / prev
        if abs(change) > 0.5: # 50% change is an anomaly
            type_label = "SPIKE" if change > 0 else "DROP"
            anomalies.append({
                "month": data[i].get('month'),
                "repo": data[i].get('repo_name'),
                "type": type_label,
                "intensity": f"{abs(change)*100:.1f}%"
            })
    return anomalies[:3] # Limit to top 3 clues

@router_v1.post("/chat", response_model=ChatResponse)
async def chat(request_request: Request, chat_request: ChatRequest):
    # ... (skipping lines)
    # 2. Execute SQL
    data = []
    # ...
    # 3. Formulate Answer
    if data:
        clues = detect_anomalies(data)
        if engine_type == "sqlbot":
            # ...
            answer = client.generate_summary(chat_request.message, data)
            if clues:
                clue_text = "\n\n🔍 **DETECTIVE CLUES FOUND:**\n" + "\n".join([f"- {c['month']} | {c['repo']} {c['type']} detected ({c['intensity']})" for c in clues])
                answer += clue_text
        else:
            answer = f"Found {len(data)} records for your query."
    # ...

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