import requests
import os
import json
import re
import base64
from typing import Optional
from dotenv import dotenv_values
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

class SQLBotClient:
    _cached_token = None

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
        # Handle empty strings from docker-compose substitution
        self.username = os.getenv("SQLBOT_USERNAME") or "admin"
        self.password = os.getenv("SQLBOT_PASSWORD") or "SQLBot@123456"
        self.datasource_id = int(os.getenv("SQLBOT_DATASOURCE_ID", "1"))
        # Support direct token (bypass login)
        self.static_token = os.getenv("SQLBOT_API_KEY")

    def _get_public_key(self) -> str:
        """Fetch the RSA public key from SQLBot."""
        url = f"{self.endpoint}/api/v1/system/config/key"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json().get("data")
                # Debug logging
                print(f"🔑 Raw Public Key Response Data: {type(data)} - {data}")
                
                if isinstance(data, dict):
                    # Try to find the key in the dict
                    if "publicKey" in data: return data["publicKey"]
                    if "rsaPublicKey" in data: return data["rsaPublicKey"]
                    if "key" in data: return data["key"]
                    if "public_key" in data: return data["public_key"]
                    # If we can't find it, dump it to string if it looks like a key, or fail
                    print("⚠️ Public key data is a dict but no known key found.")
                    return ""
                return data
        except Exception as e:
            print(f"❌ Failed to get public key: {e}")
        return ""

    def _encrypt_password(self, password: str, public_key_str: str) -> str:
        """Encrypts password using RSA public key."""
        if not public_key_str or not isinstance(public_key_str, str):
            print(f"❌ Invalid public key format: {type(public_key_str)}")
            return password

        try:
            key = RSA.importKey(public_key_str)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(password.encode())
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return password

    def _login(self) -> Optional[str]:
        # 1. Get Public Key
        public_key = self._get_public_key()
        if not public_key:
            print("❌ Cannot login without public key.")
            return None

        # 2. Encrypt Password
        encrypted_pwd = self._encrypt_password(self.password, public_key)

        # 3. Login
        url = f"{self.endpoint}/api/v1/login/access-token"
        payload = {
            "username": self.username,
            "password": encrypted_pwd,
            "grant_type": "password"
        }
        
        try:
            print(f"🔐 Logging in to SQLBot as {self.username} (Encrypted)...")
            # Using form-data as per OpenAPI spec
            res = requests.post(url, data=payload, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
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
        # 1. Use static token if configured (e.g. from .env)
        if self.static_token:
            token = self.static_token
        else:
            # 2. Or try to login/use cached login token
            token = SQLBotClient._cached_token or self._login()
            
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
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {"question": question, "datasource": self.datasource_id}
            
            print(f"📡 Requesting SQL from SQLBot...")
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if res.status_code == 401:
                print("🔄 Token expired, re-logging in...")
                SQLBotClient._cached_token = None
                headers = self._get_headers()
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