import requests
import os
import json
from typing import Optional

class SQLBotClient:
    """
    HTTP Client for communicating with DataEase SQLBot.
    """
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://localhost:8080")
        self.api_key = os.getenv("SQLBOT_API_KEY", "")

    def generate_sql(self, question: str) -> Optional[str]:
        """
        Sends natural language to SQLBot and expects a SQL response.
        """
        if not self.api_key:
            print("⚠️ SQLBOT_API_KEY not set. Falling back.")
            return None

        url = f"{self.endpoint}/api/v1/chat"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": question,
            "stream": False
        }

        try:
            print(f"📡 Sending query to SQLBot at {url}...")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Assuming standard SQLBot response format
                return data.get("sql") or data.get("content")
            else:
                print(f"❌ SQLBot Error: Status {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ SQLBot Connection Failed: {e}")
            return None

def sqlbot_text_to_sql(text: str) -> str:
    """
    Unified interface for Text-to-SQL.
    """
    client = SQLBotClient()
    return client.generate_sql(text)