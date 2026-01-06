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
            print(f"🔐 Logging in to SQLBot as {self.username} (Encrypted) ...")
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
        
        # 1. If it's a pure JSON block containing 'sql' field
        try:
            potential_json = self._extract_first_json(text)
            if potential_json and isinstance(potential_json, dict) and potential_json.get("sql"):
                return potential_json["sql"].strip()
        except:
            pass

        # 2. Try to find SQL in a specific SQL block
        match = re.search(r"```sql\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        
        # 3. If it contains a raw SELECT statement, find the core query
        # We look for SELECT and try to stop before any conversational noise or JSON
        select_match = re.search(r"(SELECT\s+.*?(?:LIMIT\s+\d+|;))", text, re.DOTALL | re.IGNORECASE)
        if select_match:
            sql = select_match.group(1).strip()
            # Clean up trailing garbage common in some LLM responses
            sql = sql.split("execute-success")[0].strip()
            return sql

        # 4. Fallback: Clean up raw text
        candidate = text.strip()
        # Truncate at common AI noise keywords
        for stopper in ["execute-success", "```json", "Explanation:"]:
            candidate = candidate.split(stopper)[0]
        
        return candidate.strip()

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

    def _ask_ai(self, prompt: str) -> str:
        """Internal helper to ask the AI a question and get full text back (handles SSE)."""
        headers = self._get_headers()
        try:
            url = f"{self.endpoint}/api/v1/chat/start"
            payload = {"question": prompt, "datasource": self.datasource_id}
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            
            if res.status_code != 200: return ""
            
            json_res = res.json()
            data = json_res.get("data", {}) if "data" in json_res else json_res
            
            # 1. Check if we already have the answer in 'records'
            records = data.get("records", [])
            full_content = ""
            if records and (records[0].get("content") or records[0].get("sql")):
                full_content = records[0].get("content") or records[0].get("sql") or ""
            
            # 2. If not, follow up with the chat_id
            else:
                chat_id = data.get("id")
                if chat_id:
                    ask_url = f"{self.endpoint}/api/v1/chat/question"
                    ask_payload = {"question": prompt, "chat_id": chat_id}
                    res = requests.post(ask_url, json=ask_payload, headers=headers, timeout=30, stream=True)
                    
                    if "text/event-stream" in res.headers.get("Content-Type", ""):
                        for line in res.iter_lines():
                            if line:
                                decoded = line.decode('utf-8')
                                if decoded.startswith("data:"):
                                    json_str = decoded[5:].strip()
                                    if json_str == "[DONE]": break
                                    try:
                                        chunk = json.loads(json_str)
                                        full_content += chunk.get("content") or chunk.get("sql") or ""
                                    except: pass
                    else:
                        try:
                            inner = res.json().get("data", {})
                            full_content = inner.get("content") or inner.get("sql") or ""
                        except: pass
            
            # 3. Clean up the response (Extract message from JSON refusal objects)
            try:
                # If the AI returned a stringified JSON object
                refusal_data = self._extract_first_json(full_content)
                if refusal_data and isinstance(refusal_data, dict):
                    if "message" in refusal_data:
                        return refusal_data["message"]
                    if "content" in refusal_data:
                        return refusal_data["content"]
            except:
                pass

            return full_content
        except Exception as e:
            print(f"❌ AI Request Error: {e}")
            return ""

    def generate_summary(self, question: str, data: list) -> str:
        """Uses the LLM to interpret the query results with a strong Detective persona."""
        if not data: return "根据调查，目前的线索（数据库）中未发现与您的请求相符的记录。"
        
        # Create a compact data summary
        data_sample = json.dumps(data[:10], ensure_ascii=False)
        prompt = f"""
<Task>
你现在是 'Open-Detective AI'，一名资深的数字化开源分析专家。
请根据以下调查结果，为 Agent（用户）提供一份专业、犀利且具有洞察力的中文分析报告。

[用户问题]: {question}
[证据数量]: 找到 {len(data)} 条相关记录。
[证据样本]: {data_sample}

[规则]:
1. 严禁回答“Found X records”这种废话。
2. 必须使用中文回答。
3. 必须指出数据中的关键点（例如：谁是冠军、什么月份是转折点、趋势是好是坏）。
4. 语气要像赛博时代的私人侦探，冷静且深刻。
5. 篇幅控制在 3-5 句。
</Task>
"""
        analysis = self._ask_ai(prompt)
        if analysis:
            # Strip any potential SQL junk the AI might have included by accident
            analysis = re.sub(r'```sql.*?```', '', analysis, flags=re.DOTALL)
            return analysis.strip()
        
        # Smat default if AI fails
        return f"报告 Agent，调查已完成。我们在数据库中锁定了 {len(data)} 条关键证据。通过初步视觉重建（见下图），该项目的演进轨迹已清晰可见。"

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
{{repos_str}}
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
        # Ensure curly braces are correctly handled in f-string
        schema_hint = schema_hint.replace("{repos_str}", repos_str)
        enhanced_question = f"{schema_hint}\nUserQuestion: {question}"

        sql = self._ask_ai(enhanced_question)
        return self.repair_sql(self._extract_sql(sql))

def sqlbot_text_to_sql(text: str) -> str:
    client = SQLBotClient()
    return client.generate_sql(text)