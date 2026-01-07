import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.backend.schemas.chat import ChatRequest, ChatResponse, FeedbackRequest
from src.backend.services.chat_service import ChatService
from src.backend.core.limiter import limiter
from datetime import datetime
import os

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(request: Request, chat_request: ChatRequest):
    pool = request.app.state.pool
    if chat_request.session_id:
        await ChatService.save_user_message(pool, chat_request.session_id, chat_request.message)
    
    history = await ChatService.get_history(pool, chat_request.session_id) if chat_request.session_id else []
    
    sql, data, engine, error = await ChatService.process_request(chat_request.message, history, pool)
    
    answer = ""
    if error:
        answer = f"数据库查询执行失败: {error}"
    elif not sql:
        answer = "报告 Agent，未能识别出有效的项目线索..."
    elif not data:
        answer = "报告 Agent，在当前数据库中未搜寻到相关线索..."
    else:
        async for chunk in ChatService.generate_answer_stream(chat_request.message, data, history, engine):
            answer += chunk
    
    if chat_request.session_id:
        await ChatService.save_assistant_message(pool, chat_request.session_id, answer, sql, data)
        
    return ChatResponse(
        answer=answer,
        sql_query=sql or "",
        data=data,
        engine_source=engine
    )

@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, chat_request: ChatRequest):
    pool = request.app.state.pool
    if chat_request.session_id:
        await ChatService.save_user_message(pool, chat_request.session_id, chat_request.message)
    
    history = await ChatService.get_history(pool, chat_request.session_id) if chat_request.session_id else []
    
    sql, data, engine, error = await ChatService.process_request(chat_request.message, history, pool)
    
    async def event_generator():
        yield json.dumps({
            "type": "meta", 
            "sql_query": sql, 
            "data": data, 
            "engine_source": engine,
            "error": error
        }) + "\n"

        full_answer = ""
        if error:
            msg = f"数据库查询执行失败: {error}"
            yield json.dumps({"type": "token", "content": msg}) + "\n"
            full_answer = msg
        elif not sql:
            msg = "报告 Agent，未能识别出有效的项目线索..."
            yield json.dumps({"type": "token", "content": msg}) + "\n"
            full_answer = msg
        elif not data:
            msg = "报告 Agent，在当前数据库中未搜寻到相关线索..."
            yield json.dumps({"type": "token", "content": msg}) + "\n"
            full_answer = msg
        else:
            async for chunk in ChatService.generate_answer_stream(chat_request.message, data, history, engine):
                yield json.dumps({"type": "token", "content": chunk}) + "\n"
                full_answer += chunk
        
        if chat_request.session_id:
            await ChatService.save_assistant_message(pool, chat_request.session_id, full_answer, sql, data)
        
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@router.post("/feedback")
async def collect_feedback(feedback: FeedbackRequest):
    entry = feedback.dict()
    entry["timestamp"] = str(datetime.now())
    os.makedirs("data", exist_ok=True)
    with open("data/feedback.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"status": "received"}