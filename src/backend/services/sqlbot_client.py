import requests
import os
import json
import re
from typing import Optional
from dotenv import dotenv_values

class SQLBotClient:
    """
    Standard Client for DataEase SQLBot using the MCP (Access Key) protocol.
    """
    def __init__(self, endpoint: Optional[str] = None):
        # Read from environment (hot-reloading enabled via _get_live_config)
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")

    def _get_live_config(self) -> dict:
        """Reads configuration directly from .env to support dynamic updates."""
        try:
            config = dotenv_values(".env")
            return {
                "key": config.get("SQLBOT_API_KEY", ""), # The Access Key
                "ds_id": config.get("SQLBOT_DATASOURCE_ID", "1")
            }
        except Exception:
            return {"key": os.getenv("SQLBOT_API_KEY", ""), "ds_id": "1"}

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return text.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        conf = self._get_live_config()
        if not conf["key"]:
            print("❌ Error: SQLBOT_API_KEY (Access Key) is missing in .env")
            return None

        # Official MCP Endpoint
        url = f"{self.endpoint}/api/v1/mcp/mcp_question"
        
        # Payload based on McpQuestion schema from openapi.json
        payload = {
            "question": question,
            "chat_id": 0,          # 0 for a new stateless request
            "token": conf["key"],  # The Access Key goes here
            "stream": False,
            "lang": "zh-CN"
        }

        try:
            print(f"📡 Dispatching to SQLBot MCP using Access Key...")
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # SQLBot MCP usually returns content or sql
                raw_content = data.get("content") or data.get("sql") or ""
                return self._extract_sql(raw_content)
            else:
                print(f"❌ SQLBot MCP Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ SQLBot Connection Failed: {e}")
            return None

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)