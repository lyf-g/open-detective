import sqlite3
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(
    title="Open-Detective API",
    description="Backend for Open-Detective",
    version="0.1.0"
)

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '../../open_detective.db')

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sql_query: str
    data: List[Dict[str, Any]]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def mock_text_to_sql(text: str) -> str:
    """
    A very simple rule-based 'AI' for the MVP.
    Real implementation will use LLM here.
    """
    text = text.lower()
    
    # improved detection logic
    repo = None
    if "vue" in text: repo = "vuejs/core"
    elif "fastapi" in text: repo = "fastapi/fastapi"
    elif "react" in text: repo = "facebook/react"
    elif "tensorflow" in text: repo = "tensorflow/tensorflow"
    
    metric = "stars" # default
    if "activity" in text: metric = "activity"
    elif "rank" in text: metric = "openrank"
    
    if repo:
        return f"SELECT month, value FROM open_digger_metrics WHERE repo_name = '{repo}' AND metric_type = '{metric}' ORDER BY month ASC"
    
    return ""

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print(f"Received message: {request.message}")
    
    # 1. Generate SQL (Mock AI)
    sql_query = mock_text_to_sql(request.message)
    
    if not sql_query:
        return ChatResponse(
            answer="Sorry, I couldn't understand the repository name. Try asking about 'vue', 'fastapi', or 'react'.",
            sql_query="",
            data=[]
        )

    # 2. Execute SQL
    data = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
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

@app.get("/health")
def health_check():
    return {"status": "ok"}