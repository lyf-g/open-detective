import requests
import os
import json
import re
from typing import Optional

class SQLBotClient:
    """
    HTTP Client for communicating with DataEase SQLBot via standard Chat API.
    """
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
        self.api_key = os.getenv("SQLBOT_API_KEY", "")
        # The datasource ID configured in SQLBot Admin
        self.datasource_id = int(os.getenv("SQLBOT_DATASOURCE_ID", "1"))

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        # Support various markdown formats returned by LLMs
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return text.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        if not self.api_key:
            print("⚠️ SQLBOT_API_KEY is missing!")
            return None

        headers = {
            "X-SQLBOT-TOKEN": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            # 1. Start a Chat Session
            start_url = f"{self.endpoint}/api/v1/chat/start"
            start_payload = {
                "question": question,
                "datasource": self.datasource_id
            }
            print(f"📡 Initializing SQLBot session: {start_url}")
            start_res = requests.post(start_url, json=start_payload, headers=headers, timeout=10)
            
            if start_res.status_code != 200:
                print(f"❌ Failed to start chat: {start_res.status_code} - {start_res.text}")
                return None
            
            chat_info = start_res.json()
            chat_id = chat_info.get("id")
            
            if not chat_id:
                print("❌ SQLBot returned no chat_id")
                return None

            # 2. Ask the actual question (if not already answered by start)
            # Some SQLBot versions process the question in 'start' if provided.
            # Let's check if the first record already has an answer.
            records = chat_info.get("records", [])
            if records and records[0].get("sql"):
                return self._extract_sql(records[0].get("sql"))

            # If not answered, call question endpoint
            ask_url = f"{self.endpoint}/api/v1/chat/question"
            ask_payload = {
                "question": question,
                "chat_id": chat_id
            }
            print(f"📡 Sending question to Chat #{chat_id}: {ask_url}")
            ask_res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30)
            
            if ask_res.status_code == 200:
                # The response for question might be the record itself
                data = ask_res.json()
                # SQLBot usually returns the SQL in 'sql' field of the record
                return self._extract_sql(data.get("sql") or data.get("content") or "")
            else:
                print(f"❌ SQLBot Ask Error: {ask_res.status_code}")
                return None

        except Exception as e:
            print(f"❌ SQLBot Integration Error: {e}")
            return None

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)