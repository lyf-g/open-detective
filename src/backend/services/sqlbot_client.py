import requests
import os
import json
import re
from typing import Optional

class SQLBotClient:
    """
    HTTP Client for DataEase SQLBot with Auto-Login capabilities.
    """
    _cached_token = None

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
        self.username = os.getenv("SQLBOT_USER", "admin")
        self.password = os.getenv("SQLBOT_PASSWORD", "SQLBot@123456")
        self.datasource_id = int(os.getenv("SQLBOT_DATASOURCE_ID", "1"))

    def _login(self) -> Optional[str]:
        """Performs login to get a valid JWT token."""
        url = f"{self.endpoint}/api/v1/login/access-token"
        # SQLBot expects form-data for login
        payload = {
            "username": self.username,
            "password": self.password
        }
        try:
            print(f"🔐 Authenticating with SQLBot as {self.username}...")
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                token = response.json().get("access_token")
                SQLBotClient._cached_token = token
                return token
            else:
                print(f"❌ Login Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Login Connection Error: {e}")
            return None

    def _get_headers(self):
        token = SQLBotClient._cached_token or self._login()
        return {
            "X-SQLBOT-TOKEN": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return text.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        headers = self._get_headers()
        if not SQLBotClient._cached_token:
            return None

        try:
            # 1. Start Chat
            start_url = f"{self.endpoint}/api/v1/chat/start"
            start_payload = {"question": question, "datasource": self.datasource_id}
            
            print(f"📡 Initializing session with SQLBot...")
            res = requests.post(start_url, json=start_payload, headers=headers, timeout=15)
            
            if res.status_code == 401: # Token might have expired
                print("🔄 Token expired, re-authenticating...")
                self._login()
                headers = self._get_headers()
                res = requests.post(start_url, json=start_payload, headers=headers, timeout=15)

            if res.status_code != 200:
                print(f"❌ SQLBot Error: {res.status_code} - {res.text}")
                return None

            data = res.json()
            # If the answer is in the start response
            records = data.get("records", [])
            if records and records[0].get("sql"):
                return self._extract_sql(records[0].get("sql"))

            # 2. Ask Question if needed
            chat_id = data.get("id")
            ask_url = f"{self.endpoint}/api/v1/chat/question"
            ask_payload = {"question": question, "chat_id": chat_id}
            
            print(f"📡 Sending query to Chat #{chat_id}...")
            res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30)
            if res.status_code == 200:
                record = res.json()
                return self._extract_sql(record.get("sql") or record.get("content") or "")
            
            return None
        except Exception as e:
            print(f"❌ SQLBot Request Failed: {e}")
            return None

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)
