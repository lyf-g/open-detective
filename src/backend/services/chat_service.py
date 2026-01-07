import os
import json
import asyncio
from typing import Optional, Tuple, AsyncGenerator
from src.backend.services.engine_factory import get_sql_engine
from src.backend.services.logger import logger
from src.backend.core.config import settings

def detect_anomalies(data: list) -> list:
    """Scans data for significant spikes or drops."""
    if len(data) < 3: return []
    threshold = settings.ANOMALY_THRESHOLD
    anomalies = []
    for i in range(1, len(data)):
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

class ChatService:
    @staticmethod
    async def save_user_message(pool, session_id: str, message: str):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)", (session_id, 'user', message))
                
                await cur.execute("SELECT count(*) as cnt FROM messages WHERE session_id = %s", (session_id,))
                res = await cur.fetchone()
                count = res.get('cnt', 0) if res else 0
                
                if count <= 1:
                    title = (message[:30] + '..') if len(message) > 30 else message
                    await cur.execute("UPDATE sessions SET title = %s WHERE id = %s", (title, session_id))

    @staticmethod
    async def save_assistant_message(pool, session_id: str, answer: str, sql: str, data: list):
        evidence_data_json = json.dumps(data) if data else None
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO messages (session_id, role, content, evidence_sql, evidence_data) VALUES (%s, %s, %s, %s, %s)",
                    (session_id, 'assistant', answer, sql, evidence_data_json)
                )

    @staticmethod
    async def get_history(pool, session_id: str) -> list:
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT role, content FROM messages WHERE session_id = %s ORDER BY id DESC LIMIT 5", (session_id,))
                    rows = await cur.fetchall()
                    return list(reversed(rows))
        except: return []

    @staticmethod
    async def process_request(message: str, history: list, pool) -> Tuple[str, list, str, str]:
        engine_type_raw = settings.SQL_ENGINE_TYPE
        engine_type = engine_type_raw.split('#')[0].strip().lower()

        sql_query = ""
        # SQLBotClient/Engine logic is synchronous (calls API). 
        # We can run it in executor to avoid blocking loop if slow? 
        # For now keep sync or refactor Client to be async. (Client uses `requests` which is sync).
        # Optimization: use httpx in Client later.
        if engine_type == "sqlbot":
            from src.backend.services.sqlbot_client import SQLBotClient
            client = SQLBotClient()
            sql_query = client.generate_sql(message, history=history)
        else:
            engine = get_sql_engine()
            sql_query = engine(message)

        data = []
        error_msg = ""
        if sql_query:
            try:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        logger.info("Executing SQL", sql=sql_query)
                        await cur.execute(sql_query)
                        data = await cur.fetchall()
            except Exception as e:
                logger.error("SQL Execution Error", error=str(e), sql=sql_query)
                error_msg = str(e)
        
        return sql_query, data, engine_type, error_msg

    @staticmethod
    async def generate_answer_stream(message: str, data: list, history: list, engine_type: str) -> AsyncGenerator[str, None]:
        if engine_type == "sqlbot":
            from src.backend.services.sqlbot_client import SQLBotClient
            client = SQLBotClient()
            # client.generate_summary_stream is synchronous generator.
            # We wrap it.
            for chunk in client.generate_summary_stream(message, data, history=history):
                yield chunk
                await asyncio.sleep(0) # Yield control
        else:
            yield f"报告 Agent，搜寻到 {len(data)} 条相关证据。具体趋势已在下方视觉重建。"
            
        clues = detect_anomalies(data)
        if clues:
             yield "\n\n🔍 **DETECTIVE CLUES FOUND:**\n" + "\n".join([f"- {c['month']} | {c['repo']} {c['type']} detected ({c['intensity']})" for c in clues])