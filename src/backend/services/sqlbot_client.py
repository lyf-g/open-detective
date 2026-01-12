import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from datetime import datetime
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
    _sql_cache = {}

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
        """Aggressive cleanup. If text looks like a JSON chart config, discard it."""
        if not text: return ""
        
        # 1. Remove Markdown Code Blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # 2. Check for Chart Configuration signatures
        if '"axis":' in text or '"type":' in text or '"series":' in text:
            return "" # Discard entirely if it's a chart config
            
        # 3. Clean residual JSON brackets
        text = re.sub(r'^\s*\{.*?\}\s*$', '', text, flags=re.DOTALL)
        text = re.sub(r'[\[\]\{\}]', '', text) # Remove remaining brackets

        # 4. Clean residual JSON artifacts (comma, quote, colon at end/start)
        text = re.sub(r'[,":\s]+$', '', text)
        text = re.sub(r'^[,":\s]+', '', text)
        
        # 5. Remove system words
        text = re.sub(r'execute-success|\[DONE\]|智能问数小助手|抱歉|无法', '', text, flags=re.IGNORECASE)
        
        return text.strip()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _ask_ai_stream(self, prompt: str):
        headers = self._get_headers()
        try:
            res = requests.post(f"{self.endpoint}/api/v1/chat/start", json={"question": prompt, "datasource": self.datasource_id}, headers=headers, timeout=20)
            if res.status_code != 200: return
            
            data = res.json().get("data", res.json())
            chat_id = data.get("id")
            if not chat_id:
                yield data.get("records", [{}])[0].get("content", "")
                return
            
            res = requests.post(f"{self.endpoint}/api/v1/chat/question", json={"question": prompt, "chat_id": chat_id}, headers=headers, timeout=30, stream=True)
            for line in res.iter_lines():
                if line:
                    d = line.decode('utf-8')
                    if d.startswith("data:"):
                        js = d[5:].strip()
                        if js == "[DONE]": break
                        try:
                            content = json.loads(js).get("content", "")
                            if content: yield content
                        except: pass
        except: pass

    def generate_summary_stream(self, question: str, data: list, history: list = []):
        if not data:
            yield "线索已断，数据库中未发现匹配记录。"
            return
            
        history_text = ""
        if history:
            history_text = "历史对话:\n" + "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-4:]]) + "\n"

        prompt = f"""
<System Override>
你现在的唯一身份是文本分析师。禁止输出任何JSON或代码块。
请阅读以下数据，写一份纯文本Markdown分析报告。
</System Override>

用户线索："{question}"
数据片段: {json.dumps(data[:15])}
"""
        yield from self._ask_ai_stream(prompt)

    def _generate_fallback_report(self, question: str, data: list) -> str:
        """Rule-based detective report when AI fails."""
        if not data: return "### 🕵️‍♂️ 侦查中断\n\n**状态**：证据链断裂。\n**结论**：目标对象未在数据库中留下可追踪痕迹。"
        
        try:
            values = [float(d.get('value') or d.get('metric_value') or 0) for d in data]
            months = [d.get('month', '未知') for d in data]
        except:
            return "### ⚠️ 逻辑溢出\n\n证据文件遭遇强力加密，暂时无法读取。"
            
        start_val = values[0]
        end_val = values[-1]
        max_val = max(values)
        min_val = min(values)
        avg_val = sum(values) / len(values)
        
        diff = end_val - start_val
        percent_change = (diff / start_val * 100) if start_val != 0 else 0
        
        trend_desc = "平稳波动"
        if percent_change > 20: trend_desc = "显著增长"
        elif percent_change < -20: trend_desc = "严重下滑"
            
        peak_idx = values.index(max_val)
        peak_date = months[peak_idx]

        return f"""[NEURAL DEDUCTION]
> 正在解析跨时区数据指纹... 目标已锁定。

# 📂 开源侦探核心审计报告

## 一、 证据概览
本次侦查聚焦于目标的波动特征。数据跨度共 `{len(data)}` 个周期。
数值在 `{min_val:.2f}` 与 `{max_val:.2f}` 之间剧烈震荡。

## 二、 行为模式识别
1. **关键异动**：在 `{peak_date}` 监测到峰值响应 `{int(max_val)}`。
2. **趋势判定**：整体呈现 **{trend_desc}** 态势（周期偏移量: `{percent_change:+.1f}%`）。
3. **活跃基准**：系统均值维持在 `{int(avg_val)}` 水平。

## 三、 侦探最终判决
目标项目目前处于 **{trend_desc}** 阶段。建议结合 `{peak_date}` 前后的核心提交记录进行深度代码审计。

[ANOMALY ALERT]
- {peak_date} | 监测到最高级别活动峰值
- 偏移量 | {percent_change:+.1f}% 相较于初始观测点
"""

    def generate_summary(self, question: str, data: list, history: list = []) -> str:
        if not data: return "线索已断，数据库中未发现匹配记录。"
        
        prompt = f"""
<System Override>
你现在的唯一身份是文本分析师。禁止输出任何JSON或代码块。
请阅读以下数据，写一份纯文本Markdown分析报告。
</System Override>

用户线索："{question}"
数据片段: {json.dumps(data[:15])}
"""
        ans = self._ask_ai(prompt)
        
        # Aggressive Refusal/Error Check
        # If it looks like JSON error or contains refusal words, kill it.
        if '{"success":false' in ans or '"message":' in ans or "小助手" in ans or "我无法" in ans or "I cannot" in ans:
             return self._generate_fallback_report(question, data)

        cleaned_ans = self.sanitize_text(ans)
        
        if not cleaned_ans:
            return self._generate_fallback_report(question, data)
            
        return cleaned_ans

    def _get_few_shot_examples(self) -> str:
        try:
            path = os.path.join(os.path.dirname(__file__), '../../../data/examples.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    examples = json.load(f)
                return "\n".join([f"Q: {e['q']}\nSQL: {e['sql']}" for e in examples])
        except: pass
        return ""

    def generate_sql(self, question: str, history: list = []) -> Optional[str]:
        # Cache Check
        cache_key = f"{question.strip().lower()}|{len(history)}"
        if cache_key in SQLBotClient._sql_cache:
            return SQLBotClient._sql_cache[cache_key]

        history_text = ""
        if history:
            history_text = "Conversation History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]]) + "\n"

        schema_context = """
Table: open_digger_metrics
Columns:
- repo_name (VARCHAR): Full GitHub repository name (e.g. 'vuejs/core', 'facebook/react')
- metric_type (VARCHAR): Metric being measured. Valid values: 'stars', 'activity', 'openrank', 'bus_factor', 'issues_new', 'issues_closed'
- month (VARCHAR): Time period in 'YYYY-MM' format
- value (DOUBLE): The numeric value of the metric
"""

        examples = self._get_few_shot_examples()

        prompt = f"""
<System>
You are Open-Detective, an expert data analyst specializing in Open Source Software metrics.
Your goal is to generate a valid MySQL query to answer the user's question.

Current Date: {datetime.now().strftime('%Y-%m-%d')}

Schema Context:
{schema_context}

Supported Repositories: {", ".join(SQLBotClient._repo_list)}

Few-Shot Examples:
{examples}

Instructions:
1. Output ONLY the raw SQL query. Do not use Markdown, code blocks (```), or explanations.
2. ALWAYS SELECT `repo_name`, `month`, and `value`.
3. Filter by `metric_type` appropriate to the question.
4. Filter by `repo_name`. If the user asks to compare multiple repositories (e.g., "vue vs react"), use `repo_name IN ('repo1', 'repo2')`.
5. ORDER BY `month` ASC.
6. Use the full repository names provided in the "Supported Repositories" list.
</System>
{history_text}
Question: {question}
"""
        result = self.repair_sql(self._extract_sql(self._ask_ai(prompt)))
        
        # Cache Result
        if result:
            if len(SQLBotClient._sql_cache) > 200:
                SQLBotClient._sql_cache.pop(next(iter(SQLBotClient._sql_cache)))
            SQLBotClient._sql_cache[cache_key] = result
            
        return result

def sqlbot_text_to_sql(text: str) -> str:
    return SQLBotClient().generate_sql(text)
