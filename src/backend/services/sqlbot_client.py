import requests
import os
import json
import re
from typing import Optional
from dotenv import dotenv_values

class SQLBotClient:
    """
    Client for DataEase SQLBot with Auto-Login using standard API.
    """
    _cached_token = None

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
        # Credentials from environment or defaults
        self.username = "admin"
        self.password = "SQLBot@123456"
        self.datasource_id = int(os.getenv("SQLBOT_DATASOURCE_ID", "1"))

    def _login(self) -> Optional[str]:
        """Fetches a JWT token using username/password."""
        url = f"{self.endpoint}/api/v1/login/access-token"
        
        # Based on openapi.json, this endpoint often accepts form-data or JSON
        # Let's try JSON first as it's cleaner
        payload = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }
        
        try:
            print(f"🔐 Logging in to SQLBot as {self.username}...")
            # Note: Many OAuth implementations require form-data for access-token
            res = requests.post(url, json=payload, timeout=10)
            
            if res.status_code != 200:
                # Fallback to form-data if JSON fails
                res = requests.post(url, data=payload, timeout=10)

            if res.status_code == 200:
                data = res.json()
                # Token response usually has 'access_token' or nested 'data'
                token = data.get("access_token") or data.get("data", {}).get("access_token")
                if token:
                    print("✅ Login successful!")
                    SQLBotClient._cached_token = token
                    return token
            
            print(f"❌ Login Failed: {res.status_code} - {res.text}")
            return None
        except Exception as e:
            print(f"❌ Login Connection Error: {e}")
            return None

    def _get_headers(self):
        # Use cached token or login
        token = SQLBotClient._cached_token
        # If we have a hardcoded token in env (for debugging), prioritize it? 
        # No, let's prioritize auto-login for UX.
        
        if not token:
            token = self._login()
            
        if not token:
            # Fallback to env var if login fails (legacy mode)
            token = os.getenv("SQLBOT_API_KEY", "")

        # Ensure Bearer prefix is present
        if token and not token.startswith("Bearer "):
            token = f"Bearer {token}"

        return {
            "X-SQLBOT-TOKEN": token,
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
        
        try:
            # 1. Start Chat Session
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {"question": question, "datasource": self.datasource_id}
            
            print(f"📡 Requesting SQL from SQLBot...")
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            
            # Handle token expiration (401)
            if res.status_code == 401:
                print("🔄 Token expired, re-logging in...")
                SQLBotClient._cached_token = None # Clear cache
                headers = self._get_headers()     # Re-login
                res = requests.post(url, json=payload, headers=headers, timeout=20)

            if res.status_code != 200:
                print(f"❌ SQLBot Error: {res.status_code} - {res.text}")
                return None

            data = res.json()
            records = data.get("records", [])
            if records and records[0].get("sql"):
                return self._extract_sql(records[0].get("sql"))

            # 2. Poll for Answer
            chat_id = data.get("id")
            if chat_id:
                ask_url = f"{self.endpoint}/api/v1/chat/question"
                ask_payload = {"question": question, "chat_id": chat_id}
                res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30)
                if res.status_code == 200:
                    record = res.json()
                    return self._extract_sql(record.get("sql") or record.get("content") or "")

            return None
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return None

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)