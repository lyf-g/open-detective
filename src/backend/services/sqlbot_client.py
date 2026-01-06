import requests
import os
import json
import re
import time
import jwt
from typing import Optional
from dotenv import dotenv_values

class SQLBotClient:
    """
    Client for DataEase SQLBot using AK/SK Signature Authentication.
    """
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")

    def _get_live_config(self) -> dict:
        try:
            config = dotenv_values(".env")
            return {
                "ak": config.get("SQLBOT_ACCESS_KEY", ""),
                "sk": config.get("SQLBOT_SECRET_KEY", ""),
                "ds_id": int(config.get("SQLBOT_DATASOURCE_ID", "1"))
            }
        except Exception:
            return {"ak": "", "sk": "", "ds_id": 1}

    def _generate_token(self, ak: str, sk: str) -> str:
        """
        Generates a JWT token signed with the Secret Key.
        Payload typically includes the Access Key (iss/sub) and expiration.
        """
        payload = {
            "iss": ak,
            "sub": ak, # Usually the AK is the subject
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600 # 1 hour validity
        }
        # DataEase sometimes uses specific claims, let's try standard first.
        # If this fails, we might need 'accessKey': ak in payload.
        payload["accessKey"] = ak 
        
        token = jwt.encode(payload, sk, algorithm="HS256")
        return token

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return text.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        conf = self._get_live_config()
        if not conf["ak"] or not conf["sk"]:
            print("❌ SQLBOT_ACCESS_KEY or SQLBOT_SECRET_KEY is missing")
            return None

        try:
            token = self._generate_token(conf["ak"], conf["sk"])
            
            headers = {
                "X-SQLBOT-TOKEN": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Standard Chat Session Start
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {
                "question": question,
                "datasource": conf["ds_id"]
            }
            
            print(f"📡 Requesting SQL from SQLBot (Signed Mode)...")
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