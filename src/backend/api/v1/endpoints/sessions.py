from fastapi import APIRouter, Request
from src.backend.schemas.chat import Session, Message
from typing import List
import uuid
import json
from datetime import datetime

router = APIRouter()

@router.post("/sessions", response_model=Session)
async def create_session(request: Request):
    session_id = str(uuid.uuid4())
    title = "New Investigation"
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO sessions (id, title) VALUES (%s, %s)", (session_id, title))
    return {"id": session_id, "title": title, "created_at": datetime.now()}

@router.get("/sessions", response_model=List[Session])
async def list_sessions(request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
            sessions = await cur.fetchall()
            return sessions

@router.get("/sessions/{session_id}/messages", response_model=List[Message])
async def get_session_messages(session_id: str, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT role, content, evidence_sql, evidence_data FROM messages WHERE session_id = %s ORDER BY id ASC", (session_id,))
            rows = await cur.fetchall()
            for row in rows:
                if row.get('evidence_data') and isinstance(row['evidence_data'], str):
                     try: row['evidence_data'] = json.loads(row['evidence_data'])
                     except: pass
            return rows