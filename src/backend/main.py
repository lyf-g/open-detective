import os
import mysql.connector
import time
import json
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.backend.services.engine_factory import get_sql_engine
from src.backend.services.logger import configure_logger, logger

def check_system_integrity():
    """Ensures critical configuration files exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # 1. Check repos.json
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    repo_path = os.path.join(data_dir, 'repos.json')
    if not os.path.exists(repo_path):
        logger.warning("repos.json not found. Creating default configuration.")
        with open(repo_path, 'w') as f:
            json.dump(["vuejs/core", "facebook/react", "fastapi/fastapi"], f, indent=2)
            
    # 2. Check .env
    env_path = os.path.join(base_dir, '.env')
    if not os.path.exists(env_path):
        logger.warning(".env not found. Please configure your environment variables.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Configure Logger
    configure_logger()
    
    # Startup: Integrity Check
    check_system_integrity()

    # Startup: Open MySQL connection with retries
    max_retries = 5
    retry_delay = 5
    
    conn = None
    for i in range(max_retries):
        try:
            logger.info("Attempting to connect to MySQL", attempt=i+1, max_retries=max_retries)
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "open_detective")
            )
            if conn.is_connected():
                logger.info("Successfully connected to MySQL.")
                app.state.db = conn
                break
        except Exception as e:
            logger.warning("MySQL not ready yet", error=str(e))
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Backend shutting down.")
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

import uuid
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Session(BaseModel):
    id: str
    title: str
    created_at: datetime

class Message(BaseModel):
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

# Version 1 Router
router_v1 = APIRouter(prefix="/api/v1")

def detect_anomalies(data: list) -> list:
    """Scans data for significant spikes or drops."""
    if len(data) < 3: return []
    
    threshold = float(os.getenv("ANOMALY_THRESHOLD", "0.5"))
    anomalies = []
    
    for i in range(1, len(data)):
        # Handle both possible column names
        prev = float(data[i-1].get('value') or data[i-1].get('metric_value') or 0)
        curr = float(data[i].get('value') or data[i].get('metric_value') or 0)
        repo = data[i].get('repo_name') or "Unknown Repository"
        
        if prev == 0: continue
        
        change = (curr - prev) / prev
        if abs(change) > threshold:
            type_label = "SPIKE" if change > 0 else "DROP"
            anomalies.append({
                "month": data[i].get('month'),
                "repo": repo,
                "type": type_label,
                "intensity": f"{abs(change)*100:.1f}%"
            })
    return anomalies[:3]

@router_v1.post("/sessions", response_model=Session)
def create_session(request: Request):
    session_id = str(uuid.uuid4())
    title = "New Investigation"
    conn = request.app.state.db
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (id, title) VALUES (%s, %s)", (session_id, title))
    conn.commit()
    cursor.close()
    return {"id": session_id, "title": title, "created_at": datetime.now()}

@router_v1.get("/sessions", response_model=List[Session])
def list_sessions(request: Request):
    cursor = request.app.state.db.cursor(dictionary=True)
    cursor.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    cursor.close()
    return sessions

@router_v1.get("/sessions/{session_id}/messages", response_model=List[Message])
def get_session_messages(session_id: str, request: Request):
    cursor = request.app.state.db.cursor(dictionary=True)
    cursor.execute("SELECT role, content, evidence_sql, evidence_data FROM messages WHERE session_id = %s ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    cursor.close()
    # Parse JSON string back to object if needed, MySQL connector might handle it or return str
    for row in rows:
        if row.get('evidence_data') and isinstance(row['evidence_data'], str):
             try: row['evidence_data'] = json.loads(row['evidence_data'])
             except: pass
    return rows

@router_v1.post("/chat", response_model=ChatResponse)
async def chat(request_request: Request, chat_request: ChatRequest):
    logger.info("Received message", message=chat_request.message, session_id=chat_request.session_id)
    
    # 1. Save User Message
    if chat_request.session_id:
        cursor = request_request.app.state.db.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
            (chat_request.session_id, 'user', chat_request.message)
        )
        # Update title if first message
        cursor.execute("SELECT count(*) FROM messages WHERE session_id = %s", (chat_request.session_id,))
        count = cursor.fetchone()[0]
        if count <= 1:
            title = (chat_request.message[:30] + '..') if len(chat_request.message) > 30 else chat_request.message
            cursor.execute("UPDATE sessions SET title = %s WHERE id = %s", (title, chat_request.session_id))
        request_request.app.state.db.commit()
        cursor.close()

    # 2. Get Engine Type
    engine_type_raw = os.getenv("SQL_ENGINE_TYPE", "mock")
    engine_type = engine_type_raw.split('#')[0].strip().lower()

    # 2.1 Fetch History
    history = []
    if chat_request.session_id:
        try:
            cursor = request_request.app.state.db.cursor(dictionary=True)
            cursor.execute("SELECT role, content FROM messages WHERE session_id = %s ORDER BY id DESC LIMIT 5", (chat_request.session_id,))
            history = list(reversed(cursor.fetchall()))
            cursor.close()
        except: pass
    
    # 3. Generate SQL
    sql_query = ""
    if engine_type == "sqlbot":
        from src.backend.services.sqlbot_client import SQLBotClient
        client = SQLBotClient()
        sql_query = client.generate_sql(chat_request.message, history=history)
    else:
        engine = get_sql_engine()
        sql_query = engine(chat_request.message)
    
    answer = ""
    data = []
    
    if not sql_query:
        answer = "报告 Agent，未能识别出有效的项目线索。请尝试输入具体项目名称（如 vue, react）。"
    else:
        # 4. Execute SQL
        try:
            logger.info("Executing SQL", sql=sql_query)
            cursor = request_request.app.state.db.cursor(dictionary=True)
            cursor.execute(sql_query)
            data = cursor.fetchall()
            cursor.close()
        except Exception as e:
            logger.error("SQL Execution Error", error=str(e), sql=sql_query)
            # Don't crash, just report error
            answer = f"数据库查询执行失败: {str(e)}"

        # 5. Formulate Answer
        if not answer and data:
            clues = detect_anomalies(data)
            if engine_type == "sqlbot":
                from src.backend.services.sqlbot_client import SQLBotClient
                client = SQLBotClient()
                answer = client.generate_summary(chat_request.message, data, history=history)
                if clues:
                    clue_text = "\n\n🔍 **DETECTIVE CLUES FOUND:**\n" + "\n".join([f"- {c['month']} | {c['repo']} {c['type']} detected ({c['intensity']})" for c in clues])
                    answer += clue_text
            else:
                answer = f"报告 Agent，搜寻到 {len(data)} 条相关证据。具体趋势已在下方视觉重建。"
                if clues:
                    clue_text = "\n\n🔍 **监测到异常波动:**\n" + "\n".join([f"- {c['month']} 发现 {c['intensity']} 的数据{c['type']}" for c in clues])
                    answer += clue_text
        elif not answer:
            answer = "报告 Agent，在当前数据库中未搜寻到相关线索。建议更换项目名称或指标再次尝试。"

    # 6. Save Assistant Message
    if chat_request.session_id:
        cursor = request_request.app.state.db.cursor()
        evidence_data_json = json.dumps(data) if data else None
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, evidence_sql, evidence_data) VALUES (%s, %s, %s, %s, %s)",
            (chat_request.session_id, 'assistant', answer, sql_query, evidence_data_json)
        )
        request_request.app.state.db.commit()
        cursor.close()

    return ChatResponse(
        answer=answer,
        sql_query=sql_query or "",
        data=data,
        engine_source=engine_type
    )

@router_v1.get("/health", response_model=HealthResponse)
def health_check(request: Request):
    db_status = False
    try:
        db_status = request.app.state.db.is_connected()
    except:
        pass
    return {"status": "ok", "version": "0.1.0", "db_connected": db_status}

@router_v1.get("/sqlbot-health")
async def sqlbot_health():
    import requests
    endpoint = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
    try:
        res = requests.get(endpoint, timeout=2)
        return {"status": "reachable", "code": res.status_code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}

app.include_router(router_v1)

@app.get("/")
def read_root():
    return {"message": "Open-Detective Backend is running!"}
