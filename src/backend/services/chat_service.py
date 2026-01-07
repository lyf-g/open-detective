import os
import json
from typing import Optional, Tuple, Generator
from src.backend.services.engine_factory import get_sql_engine
from src.backend.services.logger import logger

def detect_anomalies(data: list) -> list:
    """Scans data for significant spikes or drops."""
    if len(data) < 3: return []
    threshold = float(os.getenv("ANOMALY_THRESHOLD", "0.5"))
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
    def save_user_message(db_conn, session_id: str, message: str):
        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)", (session_id, 'user', message))
        cursor.execute("SELECT count(*) FROM messages WHERE session_id = %s", (session_id,))
        count = cursor.fetchone()[0]
        if count <= 1:
            title = (message[:30] + '..') if len(message) > 30 else message
            cursor.execute("UPDATE sessions SET title = %s WHERE id = %s", (title, session_id))
        db_conn.commit()
        cursor.close()

    @staticmethod
    def save_assistant_message(db_conn, session_id: str, answer: str, sql: str, data: list):
        cursor = db_conn.cursor()
        evidence_data_json = json.dumps(data) if data else None
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, evidence_sql, evidence_data) VALUES (%s, %s, %s, %s, %s)",
            (session_id, 'assistant', answer, sql, evidence_data_json)
        )
        db_conn.commit()
        cursor.close()

    @staticmethod
    def get_history(db_conn, session_id: str) -> list:
        try:
            cursor = db_conn.cursor(dictionary=True)
            cursor.execute("SELECT role, content FROM messages WHERE session_id = %s ORDER BY id DESC LIMIT 5", (session_id,))
            history = list(reversed(cursor.fetchall()))
            cursor.close()
            return history
        except: return []

    @staticmethod
    def process_request(message: str, history: list, db_connection) -> Tuple[str, list, str, str]:
        engine_type_raw = os.getenv("SQL_ENGINE_TYPE", "mock")
        engine_type = engine_type_raw.split('#')[0].strip().lower()

        sql_query = ""
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
                cursor = db_connection.cursor(dictionary=True)
                logger.info("Executing SQL", sql=sql_query)
                cursor.execute(sql_query)
                data = cursor.fetchall()
                cursor.close()
            except Exception as e:
                logger.error("SQL Execution Error", error=str(e), sql=sql_query)
                error_msg = str(e)
        
        return sql_query, data, engine_type, error_msg

    @staticmethod
    def generate_answer_stream(message: str, data: list, history: list, engine_type: str) -> Generator[str, None, None]:
        if engine_type == "sqlbot":
            from src.backend.services.sqlbot_client import SQLBotClient
            client = SQLBotClient()
            yield from client.generate_summary_stream(message, data, history=history)
        else:
            yield f"报告 Agent，搜寻到 {len(data)} 条相关证据。具体趋势已在下方视觉重建。"
            
        clues = detect_anomalies(data)
        if clues:
             yield "\n\n🔍 **DETECTIVE CLUES FOUND:**\n" + "\n".join([f"- {c['month']} | {c['repo']} {c['type']} detected ({c['intensity']})" for c in clues])
