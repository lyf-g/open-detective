import requests
import os
import json
import re
from typing import Optional
from dotenv import dotenv_values

class SQLBotClient:
    """
    Simple Client for DataEase SQLBot using a static Session Token (Bearer JWT).
    """
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")

    def _get_live_token(self) -> str:
        """Reads the raw token directly from the .env file."""
        # Try to read from volume mounted .env first
        try:
            config = dotenv_values(".env")
            token = config.get("SQLBOT_API_KEY")
            if token:
                return token
        except Exception:
            pass
        # Fallback to env var
        return os.getenv("SQLBOT_API_KEY", "")

    def _get_datasource_id(self) -> int:
        try:
            config = dotenv_values(".env")
            return int(config.get("SQLBOT_DATASOURCE_ID", "1"))
        except:
            return 1

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return text.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        token = self._get_live_token()
        ds_id = self._get_datasource_id()
        
        if not token:
            print("❌ SQLBOT_API_KEY is empty in .env")
            return None

        # Headers exactly as captured in browser
        headers = {
            "X-SQLBOT-TOKEN": token, # Expecting 'Bearer eyJ...'
            "Content-Type": "application/json"
        }

        try:
            # Standard Chat Session Start
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {
                "question": question,
                "datasource": ds_id
            }
            
            print(f"📡 Requesting SQL from SQLBot (Static Token Mode)...")
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if res.status_code != 200:
                print(f"❌ SQLBot Error: {res.status_code} - {res.text}")
                return None

            data = res.json()
            records = data.get("records", [])
            
            if records and records[0].get("sql"):
                return self._extract_sql(records[0].get("sql"))

            chat_id = data.get("id")
            if chat_id:
                ask_url = f"{self.endpoint}/api/v1/chat/question"
                ask_payload = {"question": question, "chat_id": chat_id}
                print(f"📡 Polling Chat #{chat_id}...")
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
