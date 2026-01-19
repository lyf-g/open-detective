import json
import csv
import io
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import StreamingResponse
from src.backend.schemas.chat import ChatRequest, ChatResponse, FeedbackRequest
from src.backend.services.chat_service import ChatService
from src.backend.core.limiter import limiter
from datetime import datetime
import os

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Chat with AI", tags=["chat"])
@limiter.limit("10/minute")
async def chat(request: Request, payload: ChatRequest):
    pool = request.app.state.pool
    if payload.session_id:
        await ChatService.save_user_message(pool, payload.session_id, payload.message)
    
    history = await ChatService.get_history(pool, payload.session_id) if payload.session_id else []
    
    # Unpack 5 values
    sql, data, engine, error, healing_logs = await ChatService.process_request(payload.message, history, pool)
    
    answer = ""
    # Prepend repair logs to answer
    if healing_logs:
        answer += "\n".join(healing_logs) + "\n\n"

    if error:
        answer += f"数据库查询执行失败: {error}"
    elif not sql:
        answer += "报告 Agent，未能识别出有效的项目线索..."
    elif not data:
        answer += "报告 Agent，在当前数据库中未搜寻到相关线索..."
    else:
        async for chunk in ChatService.generate_answer_stream(payload.message, data, history, engine):
            answer += chunk
    
    if payload.session_id:
        await ChatService.save_assistant_message(pool, payload.session_id, answer, sql, data)
        
    return ChatResponse(
        answer=answer,
        sql_query=sql or "",
        data=data,
        engine=engine
    )

@router.post("/chat/stream", summary="Stream Chat with AI", tags=["chat"])
@limiter.limit("10/minute")
async def chat_stream(request: Request, payload: ChatRequest):
    pool = request.app.state.pool
    if payload.session_id:
        await ChatService.save_user_message(pool, payload.session_id, payload.message)
    
    history = await ChatService.get_history(pool, payload.session_id) if payload.session_id else []
    
    # Unpack 5 values
    sql, data, engine, error, healing_logs = await ChatService.process_request(payload.message, history, pool)
    
    async def event_generator():
        # 1. Stream Repair Logs (Visual Self-Healing)
        full_answer = ""
        if healing_logs:
            for log in healing_logs:
                chunk = f"{log}\n\n"
                yield json.dumps({"type": "token", "content": chunk}) + "\n"
                full_answer += chunk

        # 2. Send Meta
        yield json.dumps({
            "type": "meta", 
            "sql_query": sql, 
            "data": data, 
            "engine_source": engine,
            "error": error
        }) + "\n"

        if error:
            msg = f"数据库查询执行失败: {error}"
            yield json.dumps({"type": "token", "content": msg}) + "\n"
            full_answer += msg
        elif not sql:
            msg = "报告 Agent，未能识别出有效的项目线索..."
            yield json.dumps({"type": "token", "content": msg}) + "\n"
            full_answer += msg
        elif not data:
            msg = "报告 Agent，在当前数据库中未搜寻到相关线索..."
            yield json.dumps({"type": "token", "content": msg}) + "\n"
            full_answer += msg
        else:
            async for chunk in ChatService.generate_answer_stream(payload.message, data, history, engine):
                yield json.dumps({"type": "token", "content": chunk}) + "\n"
                full_answer += chunk
        
        if payload.session_id:
            await ChatService.save_assistant_message(pool, payload.session_id, full_answer, sql, data)
        
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@router.post("/feedback", summary="Submit Feedback", tags=["chat"], response_description="Acknowledgement of feedback receipt.")
async def collect_feedback(payload: FeedbackRequest):
    entry = payload.model_dump()
    entry["timestamp"] = str(datetime.now(timezone.utc))
    os.makedirs("data", exist_ok=True)
    with open("data/feedback.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"status": "received"}

@router.get("/messages/{message_id}/export", summary="Export Message Data", tags=["chat"])
async def export_message_data(message_id: int, request: Request, format: str = "csv"):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT evidence_data FROM messages WHERE id = %s", (message_id,))
            row = await cur.fetchone()
            
    if not row or not row['evidence_data']:
        raise HTTPException(status_code=404, detail="No data found")
        
    data = json.loads(row['evidence_data']) if isinstance(row['evidence_data'], str) else row['evidence_data']
    
    if format == "json":
        return data
        
    output = io.StringIO()
    if data and isinstance(data, list):
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=data-{message_id}.csv"})