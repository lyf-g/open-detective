import os
import json
import asyncio
from typing import Optional, Tuple, AsyncGenerator
from src.backend.services.engine_factory import get_sql_engine
from src.backend.services.logger import logger
from src.backend.core.config import settings
from src.backend.services.analytics import forecast_next_months
from src.backend.services.sql_validator import validate_sql

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
            anomaly = {
                "month": data[i].get('month'),
                "repo": repo,
                "type": type_label,
                "intensity": f"{abs(change)*100:.1f}%",
                "z_score": abs(change) * 2 # Mock Z-score for now
            }
            anomalies.append(anomaly)
            logger.info("Anomaly Detected", **anomaly)
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
    async def process_request(message: str, history: list, pool) -> Tuple[str, list, str, str, list]:
        engine_type_raw = settings.SQL_ENGINE_TYPE
        engine_type = engine_type_raw.split('#')[0].strip().lower()
        repair_logs = []

        sql_query = ""
        if engine_type == "sqlbot":
            from src.backend.services.sqlbot_client import SQLBotClient
            client = SQLBotClient()
            sql_query = client.generate_sql(message, history=history)
        else:
            engine = get_sql_engine()
            sql_query = engine(message)

        # DEMO SABOTAGE: Intentionally break SQL for the demo
        if "sabotage" in message.lower() and sql_query:
            sql_query = sql_query.replace("stars", "starrrs") # Introduce typo

        data = []
        error_msg = ""
        
        # Self-Healing Loop
        max_retries = 2
        for attempt in range(max_retries):
            if not sql_query: break
            
            try:
                if not validate_sql(sql_query):
                    return "", [], engine_type, "Security Alert: Only SELECT statements are allowed.", []

                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        logger.info(f"Executing SQL (Attempt {attempt+1})", sql=sql_query)
                        await cur.execute(sql_query)
                        data = await cur.fetchall()
                
                # Add Forecast
                if data:
                    forecast = forecast_next_months(data)
                    data.extend(forecast)
                
                # If success, break loop
                error_msg = "" # Clear error if success
                break
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"SQL Error (Attempt {attempt+1})", error=error_msg)
                
                repair_logs.append(f"⚠️ **Error Detected:** {error_msg[:50]}...")
                
                # Heuristic Repair (Mock/Simple)
                if "Unknown column" in error_msg or "starrrs" in sql_query:
                    repair_logs.append("🔧 **System Protocol:** Analyzing Schema...")
                    if "starrrs" in sql_query:
                        sql_query = sql_query.replace("starrrs", "stars")
                        repair_logs.append("✅ **Patch Applied:** Corrected column 'starrrs' to 'stars'.")
                    else:
                        repair_logs.append("⚠️ **Patch Failed:** Schema mismatch. Terminating.")
                        break # Cannot fix unknown error
                else:
                    break # Unknown error, stop
        
        return sql_query, data, engine_type, error_msg, repair_logs

    @staticmethod
    def generate_deduction(data: list) -> str:
        """Generates a noir/cyberpunk style insight."""
        if not data:
            return "Scan complete. No trace found in the archives."
        
        # Simple Trend Analysis
        values = [float(d.get('value') or d.get('metric_value') or 0) for d in data if not d.get('is_forecast')]
        if len(values) < 2:
            return "Insufficient data for behavioral profiling."
            
        start, end = values[0], values[-1]
        change = (end - start) / start if start != 0 else 0
        
        if change > 0.5:
            return "Subject exhibiting explosive growth. Momentum is critical."
        elif change > 0.1:
            return "Steady upward trajectory confirmed. Systems nominal."
        elif change < -0.5:
            return "Catastrophic signal loss. Subject vital signs are fading."
        elif change < -0.1:
            return "Slow decay detected. Entropy is increasing."
        else:
            return "Pattern is stable. No significant deviations observed."

    @staticmethod
    async def generate_answer_stream(message: str, data: list, history: list, engine_type: str) -> AsyncGenerator[str, None]:
        # 1. Deduction (The "Hook")
        deduction = ChatService.generate_deduction(data)
        yield f"**[NEURAL DEDUCTION]**\n> {deduction}\n\n"
        await asyncio.sleep(0.5) # Dramatic pause

        if engine_type == "sqlbot":
            from src.backend.services.sqlbot_client import SQLBotClient
            client = SQLBotClient()
            # client.generate_summary_stream is synchronous generator.
            # We wrap it.
            for chunk in client.generate_summary_stream(message, data, history=history):
                yield chunk
                await asyncio.sleep(0)
        else:
            yield f"Evidence retrieved: {len(data)} records found.\n"
            
        clues = detect_anomalies(data)
        if clues:
             clue_text = "\n\n**[ANOMALY ALERT]**\n" + "\n".join([f"- {c['month']} | {c['repo']} {c['type']} detected ({c['intensity']})" for c in clues])
             yield clue_text