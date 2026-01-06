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
    _repo_list = []

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
        self.username = os.getenv("SQLBOT_USERNAME") or "admin"
        self.password = os.getenv("SQLBOT_PASSWORD") or "SQLBot@123456"
        self.datasource_id = int(os.getenv("SQLBOT_DATASOURCE_ID", "1"))
        self.static_token = os.getenv("SQLBOT_API_KEY")
        
        # Load known repos to help the AI map names
        if not SQLBotClient._repo_list:
            try:
                repo_path = os.path.join(os.path.dirname(__file__), '../../../data/repos.json')
                if os.path.exists(repo_path):
                    with open(repo_path, 'r') as f:
                        SQLBotClient._repo_list = json.load(f)
            except:
                pass

    def _get_public_key(self) -> str:
        """Fetch the RSA public key from SQLBot."""
        url = f"{self.endpoint}/api/v1/system/config/key"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json().get("data")
                if isinstance(data, dict):
                    return data.get("public_key") or data.get("publicKey") or ""
                return data
        except Exception as e:
            print(f"❌ Failed to get public key: {e}")
        return ""

    def _encrypt_rsa(self, text: str, public_key_str: str) -> str:
        """Encrypts text using RSA public key."""
        if not public_key_str or not isinstance(public_key_str, str):
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
        public_key = self._get_public_key()
        if not public_key: return None

        encrypted_user = self._encrypt_rsa(self.username, public_key)
        encrypted_pwd = self._encrypt_rsa(self.password, public_key)

        url = f"{self.endpoint}/api/v1/login/access-token"
        payload = {
            "username": encrypted_user,
            "password": encrypted_pwd,
            "grant_type": "password"
        }
        
        try:
            print(f"🔐 Logging in to SQLBot as {self.username} (Encrypted)...")
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
        token = self.static_token or SQLBotClient._cached_token or self._login()
        if token and not token.startswith("Bearer "):
            token = f"Bearer {token}"
        return {
            "X-SQLBOT-TOKEN": token,
            "Content-Type": "application/json"
        }

    def _extract_first_json(self, text: str) -> Optional[dict]:
        start = text.find('{')
        if start == -1: return None
        count = 0
        for i in range(start, len(text)):
            if text[i] == '{': count += 1
            elif text[i] == '}':
                count -= 1
                if count == 0:
                    try: return json.loads(text[start:i+1])
                    except: pass
        return None

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match = re.search(r"```(?:json|mysql)?\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if content.upper().startswith("SELECT"): return content
        if text.strip().upper().startswith("SELECT"):
            candidate = text.strip()
            truncate_at = candidate.find("```")
            if truncate_at != -1: candidate = candidate[:truncate_at]
            truncate_at = candidate.find("{ ", 1)
            if truncate_at != -1: candidate = candidate[:truncate_at]
            return candidate.strip()
        return text.strip()

    def repair_sql(self, sql: str) -> str:
        if not sql: return ""
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        def replace_repo(match):
            val = match.group(1)
            for full_path in SQLBotClient._repo_list:
                parts = full_path.lower().replace('/', ' ').replace('-', ' ').split()
                if val.lower() in parts or val.lower() == full_path.lower():
                    return f"'{full_path}'"
            return f"'{val}'"

        return re.sub(r"'(.*?)'", replace_repo, sql).strip()

    def generate_sql(self, question: str) -> Optional[str]:
        headers = self._get_headers()
        repos_str = ", ".join(SQLBotClient._repo_list)
        schema_hint = f"""
<SystemInstruction>
You are the 'Open-Detective AI'. Your ONLY job is to output a single MySQL query.
<DatabaseSchema>
Table: open_digger_metrics
Columns: month (string 'YYYY-MM'), value (number), repo_name (string), metric_type (string)
</DatabaseSchema>
<MetricMapping>
- stars/star/星标 -> 'stars'
- activity/活跃度/热度 -> 'activity'
- openrank/影响力 -> 'openrank'
</MetricMapping>
<KnownRepositories>
{repos_str}
</KnownRepositories>
<CriticalRules>
1. If user says 'vue', map it to 'vuejs/core'. If 'react', map to 'facebook/react'.
2. Use the FULL PATH from <KnownRepositories> whenever possible.
3. If no exact match, use: repo_name LIKE '%name%'
4. For comparison, use: WHERE (repo_name LIKE '%A%' OR repo_name LIKE '%B%')
5. ALWAYS ORDER BY month ASC.
6. DO NOT use STR_TO_DATE. 'month' is already a string.
7. Output ONLY the raw SQL. No explanation.
</CriticalRules>
</SystemInstruction>
"""
        enhanced_question = f"{schema_hint}\nUserQuestion: {question}"

        try:
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {"question": enhanced_question, "datasource": self.datasource_id}
            print(f"📡 Sending XML-Enhanced Prompt to SQLBot...")
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if res.status_code == 401:
                SQLBotClient._cached_token = None
                headers = self._get_headers()
                res = requests.post(url, json=payload, headers=headers, timeout=20)

            if res.status_code != 200: return None
            json_res = res.json()
            data = json_res.get("data", {}) if "data" in json_res else json_res
            records = data.get("records", [])
            if records and records[0].get("sql"):
                return self.repair_sql(self._extract_sql(records[0].get("sql")))

            chat_id = data.get("id")
            if chat_id:
                ask_url = f"{self.endpoint}/api/v1/chat/question"
                ask_payload = {"question": enhanced_question, "chat_id": chat_id}
                res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30, stream=True)
                if res.status_code == 200:
                    content_type = res.headers.get("Content-Type", "")
                    if "text/event-stream" in content_type:
                        full_content = ""
                        for line in res.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith("data:"):
                                    json_str = decoded_line[5:].strip()
                                    if json_str == "[DONE]": break
                                    try:
                                        chunk = json.loads(json_str)
                                        full_content += chunk.get("content") or chunk.get("sql") or ""
                                    except: pass
                        data = self._extract_first_json(full_content)
                        if data and isinstance(data, dict) and data.get("sql"):
                            return self.repair_sql(data["sql"])
                        return self.repair_sql(self._extract_sql(full_content))
                    else:
                        try:
                            json_data = res.json()
                            inner_data = json_data.get("data", {}) if "data" in json_data else json_data
                            return self.repair_sql(self._extract_sql(inner_data.get("sql") or inner_data.get("content") or ""))
                        except: return None
            return None
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return None

    def generate_summary(self, question: str, data: list) -> str:
        """Uses the LLM to interpret the query results."""
        if not data: return "No evidence found to support the investigation."
        
        # Create a compact data summary for the LLM
        data_summary = json.dumps(data[:15], ensure_ascii=False)
        prompt = f"""
<Task>
You are the 'Open-Detective AI'. Interpret the investigation results for the user.
Question: {question}
Found Records: {len(data)}
Data Sample: {data_summary}

Rules:
1. Provide a professional, concise analysis (max 3 sentences).
2. Highlight key trends, peaks, or comparison winners.
3. Use a tone suitable for a digital detective.
4. Response in the same language as the user question.
</Task>
"""
        headers = self._get_headers()
        try:
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {"question": prompt, "datasource": self.datasource_id}
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            if res.status_code == 200:
                full_text = res.json().get("data", {}).get("records", [{}])[0].get("content") or ""
                # If content is empty, it might be a stream? Let's simplify for now
                if full_text: return full_text
            return f"Investigation complete. Found {len(data)} data points correlating to your request."
        except:
            return f"Found {len(data)} records for your query."

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)
