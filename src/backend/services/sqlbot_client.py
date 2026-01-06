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

    def _encrypt_rsa(self, text: str, public_key_str: str) -> str:
        """Encrypts text using RSA public key."""
        if not public_key_str or not isinstance(public_key_str, str):
            print(f"❌ Invalid public key format: {type(public_key_str)}")
            return text

        try:
            key = RSA.importKey(public_key_str)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(text.encode())
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return text

    def _login(self) -> Optional[str]:
        # 1. Get Public Key
        public_key = self._get_public_key()
        if not public_key:
            print("❌ Cannot login without public key.")
            return None

        # 2. Encrypt Credentials
        encrypted_user = self._encrypt_rsa(self.username, public_key)
        encrypted_pwd = self._encrypt_rsa(self.password, public_key)

        # 3. Login
        url = f"{self.endpoint}/api/v1/login/access-token"
        payload = {
            "username": encrypted_user,
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

    def _extract_first_json(self, text: str) -> Optional[dict]:
        """Finds and parses the first valid JSON object in a string."""
        start = text.find('{')
        if start == -1: return None
        
        count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                count += 1
            elif text[i] == '}':
                count -= 1
                if count == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except:
                        pass
        return None

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        
        # 1. Try to find SQL in a specific SQL block
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        
        # 2. Try to find SQL in any code block if it starts with SELECT
        match = re.search(r"```(?:json|mysql)?\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if content.upper().startswith("SELECT"):
                return content
        
        # 3. If it looks like a raw SELECT statement
        if text.strip().upper().startswith("SELECT"):
            # Truncate at next block or JSON to avoid trailing junk
            candidate = text.strip()
            truncate_at = candidate.find("```")
            if truncate_at != -1: candidate = candidate[:truncate_at]
            truncate_at = candidate.find("{", 1) # Ignore the starting { if it's a JSON
            if truncate_at != -1: candidate = candidate[:truncate_at]
            return candidate.strip()

        return text.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        headers = self._get_headers()
        
        # Add explicit mapping hint to bridge the semantic gap
        schema_hint = """
        ### DATABASE MAPPING RULES ###
        1. When user says 'star' or '星标', ALWAYS use `metric_type` = 'stars' (plural).
        2. When user says '活跃度' or 'activity', use `metric_type` = 'activity'.
        3. When user says '影响力' or 'openrank', use `metric_type` = 'openrank'.
        4. When user says '公交系数' or 'bus factor', use `metric_type` = 'bus_factor'.
        5. Column `repo_name` contains project names like 'vuejs/core'.
        6. Column `value` is the numeric metric value.
        7. Column `month` is the time dimension (e.g. '2023-01').
        """
        enhanced_question = question + "\n" + schema_hint

        try:
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {"question": enhanced_question, "datasource": self.datasource_id}
            
            print(f"📡 Requesting SQL from SQLBot with enhanced prompt...")
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if res.status_code == 401:
                print("🔄 Token expired, re-logging in...")
                SQLBotClient._cached_token = None
                headers = self._get_headers()
                res = requests.post(url, json=payload, headers=headers, timeout=20)

            if res.status_code != 200:
                print(f"❌ SQLBot Error: {res.status_code} - {res.text}")
                return None

            json_res = res.json()
            print(f"🔍 SQLBot Response: {json.dumps(json_res, ensure_ascii=False)}")
            
            # Unwrap 'data' field if it exists (DataEase API wrapper)
            data = json_res.get("data", {}) if "data" in json_res else json_res

            records = data.get("records", [])
            if records and records[0].get("sql"):
                return self._extract_sql(records[0].get("sql"))

            chat_id = data.get("id")
            if chat_id:
                ask_url = f"{self.endpoint}/api/v1/chat/question"
                ask_payload = {"question": enhanced_question, "chat_id": chat_id}
                print(f"📡 Asking Question to chat_id {chat_id} with enhanced prompt...")
                res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30, stream=True)
                
                print(f"🔍 Question Response Code: {res.status_code}")

                if res.status_code == 200:
                    content_type = res.headers.get("Content-Type", "")
                    if "text/event-stream" in content_type:
                        print("🌊 Detected SSE Stream. Parsing...")
                        full_content = ""
                        for line in res.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith("data:"):
                                    json_str = decoded_line[5:].strip()
                                    if json_str == "[DONE]": break
                                    try:
                                        chunk = json.loads(json_str)
                                        # Accumulate content
                                        content = chunk.get("content") or chunk.get("sql") or ""
                                        full_content += content
                                    except json.JSONDecodeError:
                                        pass
                        
                        print(f"🌊 Stream finished. Length: {len(full_content)}")
                        
                        # A. Try to find the first JSON and extract 'sql'
                        data = self._extract_first_json(full_content)
                        if data and isinstance(data, dict):
                            if data.get("success") is False:
                                print(f"❌ SQLBot Refused: {data.get('message')}")
                                return ""
                            if data.get("sql"):
                                return data["sql"]

                        # B. Fallback to regex extraction from the whole text
                        return self._extract_sql(full_content)
                    else:
                        # Standard JSON response
                        try:
                            json_data = res.json()
                            # Handle wrapped 'data'
                            inner_data = json_data.get("data", {}) if "data" in json_data else json_data
                            return self._extract_sql(inner_data.get("sql") or inner_data.get("content") or "")
                        except json.JSONDecodeError:
                             print(f"❌ JSON Decode Error. Body: {res.text[:500]}")
                             return None
                else:
                    print(f"❌ Question Failed: {res.text}")

            return None
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            import traceback
            traceback.print_exc()
            return None

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)