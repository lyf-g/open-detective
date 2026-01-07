from fastapi import APIRouter, Request
from src.backend.schemas.chat import Session, Message
from typing import List
import uuid
import json
from datetime import datetime

router = APIRouter()

@router.post("/sessions", response_model=Session)
def create_session(request: Request):
    session_id = str(uuid.uuid4())
    title = "New Investigation"
    conn = request.app.state.db
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (id, title) VALUES (%s, %s)", (session_id, title))
    conn.commit()
    cursor.close()
    return {"id": session_id, "title": title, "created_at": datetime.now()}

@router.get("/sessions", response_model=List[Session])
def list_sessions(request: Request):
    cursor = request.app.state.db.cursor(dictionary=True)
    cursor.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    cursor.close()
    return sessions

@router.get("/sessions/{session_id}/messages", response_model=List[Message])
def get_session_messages(session_id: str, request: Request):
    cursor = request.app.state.db.cursor(dictionary=True)
    cursor.execute("SELECT role, content, evidence_sql, evidence_data FROM messages WHERE session_id = %s ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    cursor.close()
    for row in rows:
        if row.get('evidence_data') and isinstance(row['evidence_data'], str):
             try: row['evidence_data'] = json.loads(row['evidence_data'])
             except: pass
    return rows
