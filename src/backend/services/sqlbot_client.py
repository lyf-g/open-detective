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
                with open(repo_path, 'r') as f:
                    SQLBotClient._repo_list = json.load(f)
            except:
                pass

    # ... (skipping unchanged _get_public_key, _encrypt_rsa, _login, _get_headers, _extract_first_json, _extract_sql)

    def repair_sql(self, sql: str) -> str:
        """
        Post-processes the LLM output to fix common mistakes:
        1. Strips SQL comments.
        2. Replaces shorthand repo names with full paths from the known list.
        """
        if not sql: return ""
        
        # 1. Strip SQL comments (trailing and block)
        sql = re.sub(r'--.*$', '', sql)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # 2. Auto-map shorthands to full paths
        # We look for strings inside single quotes
        def replace_repo(match):
            val = match.group(1)
            # Try to find a match in our known repo list
            for full_path in SQLBotClient._repo_list:
                # If the shorthand is part of the full path (e.g. 'vue' in 'vuejs/core')
                # and the full path is unique enough
                parts = full_path.lower().replace('/', ' ').replace('-', ' ').split()
                if val.lower() in parts or val.lower() == full_path.lower():
                    return f"'{full_path}'"
            return f"'{val}'"

        # Regex to find 'anything'
        repaired_sql = re.sub(r"'(.*?)'", replace_repo, sql)
        
        return repaired_sql.strip()

    def generate_sql(self, question: str) -> Optional[str]:
        headers = self._get_headers()
        # ... (rest of the logic remains, but we will wrap the return value)
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
4. For comparison, use: WHERE repo_name IN ('path1', 'path2', ...)
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
            # print(f"DEBUG PROMPT: {enhanced_question}") # Truncated for token efficiency
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
                return self.repair_sql(self._extract_sql(records[0].get("sql")))

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
                                return self.repair_sql(data["sql"])

                        # B. Fallback to regex extraction from the whole text
                        return self.repair_sql(self._extract_sql(full_content))
                    else:
                        # Standard JSON response
                        try:
                            json_data = res.json()
                            # Handle wrapped 'data'
                            inner_data = json_data.get("data", {}) if "data" in json_data else json_data
                            raw_sql = inner_data.get("sql") or inner_data.get("content") or ""
                            return self.repair_sql(self._extract_sql(raw_sql))

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