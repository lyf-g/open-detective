import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status

from src.backend.schemas.chat import Message, Session

router = APIRouter()


@router.post("/sessions", response_model=Session, summary="Create New Session")
async def create_session(request: Request):
    session_id = str(uuid.uuid4())
    title = "New Investigation"
    pool = request.app.state.pool
    async with pool.acquire() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO sessions (id, title) VALUES (%s, %s)", (session_id, title),
        )
    return {"id": session_id, "title": title, "created_at": datetime.now(timezone.utc)}


@router.get("/sessions", response_model=list[Session], summary="List All Sessions")
async def list_sessions(request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT id, title, created_at FROM sessions ORDER BY created_at DESC",
        )
        sessions = await cur.fetchall()
        return sessions


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[Message],
    summary="Get Session Messages",
)
async def get_session_messages(session_id: str, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, role, content, evidence_sql, evidence_data FROM messages WHERE session_id = %s ORDER BY id ASC",
                (session_id,),
            )
            rows = await cur.fetchall()
            for row in rows:
                if row.get("evidence_data") and isinstance(row["evidence_data"], str):
                    try:
                        row["evidence_data"] = json.loads(row["evidence_data"])
                    except json.JSONDecodeError:
                        pass
            return rows


@router.get("/sessions/{session_id}/export", summary="Export Session as Markdown", response_description="The generated markdown file content.")
async def export_session(session_id: str, request: Request):
    messages = await get_session_messages(session_id, request)

    md = f"# Investigation Session {session_id}\n\n"
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        md += f"### {role}\n{content}\n\n"
        if msg.get("evidence_sql"):
            md += f"```sql\n{msg['evidence_sql']}\n```\n\n"

    return Response(
        content=md,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=session-{session_id}.md",
        },
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session",
)
async def delete_session(session_id: str, request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Manually delete messages first to avoid FK constraint issues
            await cur.execute(
                "DELETE FROM messages WHERE session_id = %s", (session_id,),
            )

            await cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
