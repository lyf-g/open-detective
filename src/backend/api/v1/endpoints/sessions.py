from fastapi import APIRouter, Request, Response
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
            await cur.execute("SELECT id, role, content, evidence_sql, evidence_data FROM messages WHERE session_id = %s ORDER BY id ASC", (session_id,))
            rows = await cur.fetchall()
            for row in rows:
                if row.get('evidence_data') and isinstance(row['evidence_data'], str):
                     try: row['evidence_data'] = json.loads(row['evidence_data'])
                     except: pass
            return rows

@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str, request: Request):
    messages = await get_session_messages(session_id, request)
    
    md = f"# Investigation Session {session_id}\n\n"
    for msg in messages:
        role = msg['role'].upper()
        content = msg['content']
        md += f"### {role}\n{content}\n\n"
        if msg.get('evidence_sql'):
            md += f"```sql\n{msg['evidence_sql']}\n```\n\n"
            
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=session-{session_id}.md"}
    )

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Manually delete messages first to avoid FK constraint issues
            # (In case ON DELETE CASCADE is missing in the running DB)
            await cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
            
            await cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            if cur.rowcount == 0:
                # If messages existed but session didn't (unlikely), we might still want to return success or 404.
                # If we deleted messages, we technically acted. 
                # But strictly speaking, if session didn't exist, it's a 404 or success (idempotent).
                # Checking session existence first would be cleaner, but extra query.
                # If delete sessions returns 0, and we just deleted messages, it means the session row wasn't there.
                # Let's assume 404 if session row wasn't touched.
                return Response(status_code=404)
    return Response(status_code=204)