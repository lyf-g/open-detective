import requests
import os
import json
import re
from typing import Optional
from dotenv import dotenv_values

class SQLBotClient:
    """
    Refined Client for DataEase SQLBot using live-reloaded JWT Token.
    """
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
        self.datasource_id = int(os.getenv("SQLBOT_DATASOURCE_ID", "1"))

    def _get_live_token(self) -> str:
        """Reads the token directly from the .env file to support hot-updates."""
        config = dotenv_values(".env")
        return config.get("SQLBOT_API_KEY", "")

    def _extract_sql(self, text: str) -> str:
# ... (rest of the functions)
    def generate_sql(self, question: str) -> Optional[str]:
        api_key = self._get_live_token()
        if not api_key:
            print("❌ Error: SQLBOT_API_KEY is not set in .env (live check failed)")
            return None

        # Headers exactly as captured in your browser
        headers = {
            "X-SQLBOT-TOKEN": api_key, 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            # 1. Initialize session
            start_url = f"{self.endpoint}/api/v1/chat/start"
            payload = {
                "question": question,
                "datasource": self.datasource_id
            }
            
            print(f"📡 Initializing SQLBot session...")
            res = requests.post(start_url, json=payload, headers=headers, timeout=15)
            
            if res.status_code != 200:
                print(f"❌ SQLBot Error: {res.status_code} - {res.text}")
                return None

            data = res.json()
            
            # 2. Check if answer is already present (SQLBot often answers immediately in /start)
            records = data.get("records", [])
            if records and records[0].get("sql"):
                return self._extract_sql(records[0].get("sql"))

            # 3. Fallback to /question if no records found
            chat_id = data.get("id")
            if chat_id:
                ask_url = f"{self.endpoint}/api/v1/chat/question"
                ask_payload = {"question": question, "chat_id": chat_id}
                print(f"📡 Polling SQLBot for answer (Chat #{chat_id})...")
                ask_res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30)
                if ask_res.status_code == 200:
                    record = ask_res.json()
                    return self._extract_sql(record.get("sql") or record.get("content") or "")

            return None
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return None

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)