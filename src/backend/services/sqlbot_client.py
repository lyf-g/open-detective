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
        
        if not SQLBotClient._repo_list:
            try:
                repo_path = os.path.join(os.path.dirname(__file__), '../../../data/repos.json')
                if os.path.exists(repo_path):
                    with open(repo_path, 'r') as f:
                        SQLBotClient._repo_list = json.load(f)
            except:
                pass

    def _get_public_key(self) -> str:
        url = f"{self.endpoint}/api/v1/system/config/key"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json().get("data")
                if isinstance(data, dict):
                    return data.get("public_key") or data.get("publicKey") or ""
                return data
        except: pass
        return ""

    def _encrypt_rsa(self, text: str, public_key_str: str) -> str:
        if not public_key_str or not isinstance(public_key_str, str): return text
        try:
            key = RSA.importKey(public_key_str)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(text.encode())
            return base64.b64encode(encrypted).decode('utf-8')
        except: return text

    def _login(self) -> Optional[str]:
        pk = self._get_public_key()
        if not pk: return None
        payload = {
            "username": self._encrypt_rsa(self.username, pk),
            "password": self._encrypt_rsa(self.password, pk),
            "grant_type": "password"
        }
        try:
            res = requests.post(f"{self.endpoint}/api/v1/login/access-token", data=payload, timeout=10)
            if res.status_code == 200:
                token = res.json().get("data", {}).get("access_token") or res.json().get("access_token")
                SQLBotClient._cached_token = token
                return token
        except: pass
        return None

    def _get_headers(self):
        token = self.static_token or SQLBotClient._cached_token or self._login()
        if token and not token.startswith("Bearer "): token = f"Bearer {token}"
        return {"X-SQLBOT-TOKEN": token, "Content-Type": "application/json"}

    def _extract_sql(self, text: str) -> str:
        if not text: return ""
        # 1. Clean JSON artifacts first
        text = re.sub(r'\{\"success\":.*?\}(?=\s|SELECT|$)', '', text, flags=re.DOTALL)
        # 2. Extract SQL block
        match = re.search(r"```sql\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        # 3. Extract raw SELECT
        match = re.search(r"(SELECT\s+.*?(?:LIMIT\s+\d+|;))", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).split("execute-success")[0].strip()
        return text.strip()

    def repair_sql(self, sql: str) -> str:
        if not sql: return ""
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Metric Aliasing Map
        metric_map = {
            "'star'": "'stars'",
            "'issue'": "'issues_new'",
            "'issues'": "'issues_new'",
            "'rank'": "'openrank'",
            "'activity'": "'activity'"
        }
        for k, v in metric_map.items():
            sql = sql.replace(k, v)

        def repl(m):
            v = m.group(1)
            for p in SQLBotClient._repo_list:
                if v.lower() in p.lower().replace('/', ' ').split() or v.lower() == p.lower():
                    return f"'{p}'"
            return f"'{v}'"
        return re.sub(r"'(.*?)'", repl, sql).strip()

    def sanitize_text(self, text: str) -> str:
        """Lightweight cleanup of system artifacts."""
        if not text: return ""
        # Remove raw SQL fragments if any leaked
        text = re.sub(r'SELECT\s+.*?\s+LIMIT\s+\d+', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Remove system words
        text = re.sub(r'execute-success|\[DONE\]|智能问数小助手|抱歉|无法', '', text, flags=re.IGNORECASE)
        # Strip potential JSON wrappers if model hallucinates them despite instructions
        if text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                # If it's pure JSON, try to extract a 'message' or 'content' field, otherwise discard
                js = json.loads(text)
                return js.get('answer', js.get('message', ''))
            except: pass
        return text.strip()

    def _ask_ai(self, prompt: str) -> str:
        headers = self._get_headers()
        try:
            res = requests.post(f"{self.endpoint}/api/v1/chat/start", json={"question": prompt, "datasource": self.datasource_id}, headers=headers, timeout=20)
            if res.status_code != 200: return ""
            data = res.json().get("data", res.json())
            chat_id = data.get("id")
            if not chat_id: return data.get("records", [{}])[0].get("content", "")
            
            res = requests.post(f"{self.endpoint}/api/v1/chat/question", json={"question": prompt, "chat_id": chat_id}, headers=headers, timeout=30, stream=True)
            full = ""
            for line in res.iter_lines():
                if line:
                    d = line.decode('utf-8')
                    if d.startswith("data:"):
                        js = d[5:].strip()
                        if js == "[DONE]": break
                        try: full += json.loads(js).get("content", "")
                        except: pass
            return full
        except: return ""

    def generate_summary(self, question: str, data: list, history: list = []) -> str:
        if not data: return "线索已断，数据库中未发现匹配记录。"
        
        history_text = ""
        if history:
            history_text = "历史对话:\n" + "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-4:]]) + "\n"

        prompt = f"""
你现在是 'Open-Detective'，一位敏锐的开源情报侦探。
用户仅提供了一个模糊的线索（"{question}"），你需要通过分析以下数据证据，还原项目的真实状况。

**绝对规则：**
1. **只输出纯文本分析报告**（Markdown格式）。
2. **严禁输出任何 JSON、代码块或图表配置**（前端已有图表，你只负责解说）。
3. 语气专业、犀利、有洞察力。

**报告结构：**

### 📂 案件档案：[项目名称] [指标] 深度追踪

**📊 关键证据：**
*   (列出3个关键数据点，如峰值月、增长倍数、当前值，**加粗数字**)

**📉 侦探分析：**
(一段约100字的叙述性分析。描述曲线的起伏。例如：“该项目在202x年经历爆发式增长，随后...”)

**🕵️‍♂️ 最终判决：**
(一句话定性，例如“处于黄金爆发期”、“进入平稳成熟期”或“需警惕活跃度下滑”。)

**数据证据 (前15条):** {json.dumps(data[:15])}
**上下文:** {history_text}
"""
        ans = self._ask_ai(prompt)
        return self.sanitize_text(ans) or f"调查完成。锁定 {len(data)} 条证据，具体趋势见下方图表。"

    def generate_sql(self, question: str, history: list = []) -> Optional[str]:
        history_text = ""
        if history:
            history_text = "Conversation History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]]) + "\n"

        prompt = f"""
<System>
You are 'Open-Detective'. Output ONLY raw MySQL.
RULES:
1. ALWAYS SELECT repo_name, month, value.
2. Use full paths: {", ".join(SQLBotClient._repo_list)}
3. ORDER BY month ASC.
4. If input is short keywords (e.g. "react star"), assume it is a request for monthly trend data.
</System>
{history_text}
Question: {question}
"""
        return self.repair_sql(self._extract_sql(self._ask_ai(prompt)))

def sqlbot_text_to_sql(text: str) -> str:
    return SQLBotClient().generate_sql(text)
