import base64
import json
import os
import re
from datetime import datetime

import requests
import structlog
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from tenacity import retry, stop_after_attempt, wait_fixed

from src.backend.core.config import settings

logger = structlog.get_logger()


class SQLBotClient:
    _cached_token = None
    _sql_cache = {}

    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint or settings.SQLBOT_ENDPOINT
        self.username = settings.SQLBOT_USERNAME
        self.password = settings.SQLBOT_PASSWORD.get_secret_value()
        self.datasource_id = settings.SQLBOT_DATASOURCE_ID
        self.static_token = settings.SQLBOT_API_KEY.get_secret_value()
        self.timeout = settings.SQLBOT_TIMEOUT
        self.repo_list = settings.ALLOWED_REPOS

    def _get_public_key(self) -> str:
        url = f"{self.endpoint}/api/v1/system/config/key"
        try:
            res = requests.get(url, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json().get("data")
                if isinstance(data, dict):
                    return data.get("public_key") or data.get("publicKey") or ""
                return data
        except Exception as e:
            logger.error("failed_to_get_public_key", error=str(e), url=url)
        return ""

    def _encrypt_rsa(self, text: str, public_key_str: str) -> str:
        if not public_key_str or not isinstance(public_key_str, str):
            return text
        try:
            key = RSA.importKey(public_key_str)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(text.encode())
            return base64.b64encode(encrypted).decode("utf-8")
        except Exception as e:
            logger.error("rsa_encryption_failed", error=str(e))
            return text

    def _login(self) -> str | None:
        pk = self._get_public_key()
        if not pk:
            return None
        payload = {
            "username": self._encrypt_rsa(self.username, pk),
            "password": self._encrypt_rsa(self.password, pk),
            "grant_type": "password",
        }
        try:
            res = requests.post(
                f"{self.endpoint}/api/v1/login/access-token", data=payload, timeout=self.timeout,
            )
            if res.status_code == 200:
                token = res.json().get("data", {}).get(
                    "access_token",
                ) or res.json().get("access_token")
                SQLBotClient._cached_token = token
                return token
            logger.error("login_failed", status_code=res.status_code, body=res.text)
        except Exception as e:
            logger.error("login_exception", error=str(e))
        return None

    def _get_headers(self):
        token = self.static_token or SQLBotClient._cached_token or self._login()
        if token and not token.startswith("Bearer "):
            token = f"Bearer {token}"
        return {
            "X-SQLBOT-TOKEN": token,
            "Content-Type": "application/json",
            "User-Agent": "Open-Detective/1.0",
        }

    def _extract_sql(self, text: str) -> str:
        if not text:
            return ""
        # 1. Clean JSON artifacts first
        text = re.sub(r"\{\"success\":.*?\}(?=\s|SELECT|$)", "", text, flags=re.DOTALL)
        # 2. Extract SQL block
        match = re.search(r"```sql\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # 3. Extract raw SELECT
        match = re.search(
            r"(SELECT\s+.*?(?:LIMIT\s+\d+|;))", text, re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).split("execute-success")[0].strip()
        return text.strip()

    def repair_sql(self, sql: str) -> str:
        if not sql:
            return ""
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # Metric Aliasing Map
        metric_map = {
            "star": "stars",
            "issue": "issues_new",
            "issues": "issues_new",
            "rank": "openrank",
            "activity": "activity",
        }
        for k, v in metric_map.items():
            sql = re.sub(rf"'{k}'", f"'{v}'", sql, flags=re.IGNORECASE)

        def repl(m):
            v = m.group(1)
            for p in self.repo_list:
                if (
                    v.lower() in p.lower().replace("/", " ").split()
                    or v.lower() == p.lower()
                ):
                    return f"'{p}'"
            return f"'{v}'"

        return re.sub(r"'(.*?)'", repl, sql).strip()

    def sanitize_text(self, text: str) -> str:
        """Aggressive cleanup. If text looks like a JSON chart config, discard it."""
        if not text:
            return ""

        # 1. Remove Markdown Code Blocks
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # 2. Check for Chart Configuration signatures
        if '"axis":' in text or '"type":' in text or '"series":' in text:
            return ""  # Discard entirely if it's a chart config

        # 3. Clean residual JSON brackets and artifacts
        text = re.sub(r"^\s*\{.*?\}\s*$", "", text, flags=re.DOTALL)
        text = re.sub(r"[\[\]\{\}]", "", text)  # Remove remaining brackets

        # 4. Clean residual JSON artifacts and system words
        text = re.sub(
            r'^[,":\s]+|[,":\s]+$|execute-success|\[DONE\]|智能问数小助手|抱歉|无法',
            "",
            text,
            flags=re.IGNORECASE,
        )

        return text.strip()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _ask_ai(self, prompt: str) -> str:
        headers = self._get_headers()
        try:
            res = requests.post(
                f"{self.endpoint}/api/v1/chat/start",
                json={"question": prompt, "datasource": self.datasource_id},
                headers=headers,
                timeout=self.timeout,
            )
            if res.status_code != 200:
                return ""
            data = res.json().get("data", res.json())
            chat_id = data.get("id")
            if not chat_id:
                return data.get("records", [{}])[0].get("content", "")

            res = requests.post(
                f"{self.endpoint}/api/v1/chat/question",
                json={"question": prompt, "chat_id": chat_id},
                headers=headers,
                timeout=self.timeout,
                stream=True,
            )
            full = ""
            for line in res.iter_lines():
                if line:
                    d = line.decode("utf-8")
                    if d.startswith("data:"):
                        js = d[5:].strip()
                        if js == "[DONE]":
                            break
                        try:
                            full += json.loads(js).get("content", "")
                        except:
                            pass
            return full
        except:
            return ""

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _ask_ai_stream(self, prompt: str):
        headers = self._get_headers()
        try:
            res = requests.post(
                f"{self.endpoint}/api/v1/chat/start",
                json={"question": prompt, "datasource": self.datasource_id},
                headers=headers,
                timeout=self.timeout,
            )
            if res.status_code != 200:
                return

            data = res.json().get("data", res.json())
            chat_id = data.get("id")
            if not chat_id:
                yield data.get("records", [{}])[0].get("content", "")
                return

            res = requests.post(
                f"{self.endpoint}/api/v1/chat/question",
                json={"question": prompt, "chat_id": chat_id},
                headers=headers,
                timeout=self.timeout,
                stream=True,
            )
            for line in res.iter_lines():
                if line:
                    d = line.decode("utf-8")
                    if d.startswith("data:"):
                        js = d[5:].strip()
                        if js == "[DONE]":
                            break
                        try:
                            content = json.loads(js).get("content", "")
                            if content:
                                yield content
                        except:
                            pass
        except:
            pass

    def generate_summary_stream(self, question: str, data: list, history: list = []):
        # Use robust non-streaming generation to ensure fallback is applied
        full_response = self.generate_summary(question, data, history)

        # Simulate streaming for UX
        chunk_size = 20
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i : i + chunk_size]

    def _generate_fallback_report(self, question: str, data: list) -> str:
        """Rule-based detective report when AI fails, formatted as clean Markdown."""
        if not data:
            return "### 🕵️‍♂️ 侦查中断\n\n**状态**：证据链断裂。\n**结论**：目标对象未在数据库中留下可追踪痕迹。"

        try:
            values = [float(d.get("value") or d.get("metric_value") or 0) for d in data]
            months = [d.get("month", "未知") for d in data]
            repo = data[0].get("repo_name", "Unknown Target")
        except:
            return "### ⚠️ 逻辑溢出\n\n证据文件遭遇强力加密，暂时无法读取。"

        start_val, end_val = values[0], values[-1]
        max_val, min_val = max(values), min(values)
        avg_val = sum(values) / len(values)
        percent_change = (
            ((end_val - start_val) / start_val * 100) if start_val != 0 else 0
        )
        peak_date = months[values.index(max_val)]

        trend_desc = "平稳"
        if percent_change > 20:
            trend_desc = "显著增长"
        elif percent_change < -20:
            trend_desc = "明显下滑"

        report = f"""# {repo} 核心仓库活动分析报告

## 一、 数据概览
本次分析基于 `{repo}` 仓库在 **{months[0]} 至 {months[-1]}** 期间的活动数据。

- **分析周期**：共 {len(months)} 个月。
- **数据范围**：月度指标值在 **{min_val:.2f}** 至 **{max_val:.2f}** 之间波动。
- **总体态势**：{trend_desc} (变化幅度 {percent_change:+.1f}%)。

## 二、 核心发现：关键模式识别
通过对时序数据的分析，我们识别出以下关键模式：

1. **峰值活动 ({peak_date})**
   - **现象**：达到观察期内最高值 **{max_val:.2f}**。
   - **分析**：可能对应重大版本发布或社区事件。

2. **平均水平**
   - **现象**：全周期平均值为 **{avg_val:.2f}**。
   - **分析**：反映了项目的基准活跃度。

## 三、 结论与建议
1. **模式确认**：项目在观测期内呈现**{trend_desc}**趋势。
2. **后续建议**：建议重点回溯 **{peak_date}** 前后的代码提交记录，以确认驱动峰值的具体原因。
"""
        return report

    def generate_summary(self, question: str, data: list, history: list = []) -> str:
        if not data:
            return "线索已断，数据库中未发现匹配记录。"

        prompt = f"""
请分析以下开源项目数据并生成一份专业的Markdown分析报告。

要求：
1. 报告标题为“数据分析报告”。
2. 使用清晰的Markdown格式（标题、列表）。
3. 重点分析数据趋势、峰值和异常点。
4. 语言风格专业、客观。

用户问题："{question}"
数据片段: {json.dumps(data[:15])}
"""
        ans = self._ask_ai(prompt)

        # Aggressive Refusal/Error Check
        # If it looks like JSON error or contains refusal words, kill it.
        refusal_keywords = [
            '{"success":false',
            '"message":',
            "小助手",
            "我无法",
            "I cannot",
            "超出了我的能力范围",
            "beyond my capabilities",
            "unable to generate",
            "I can only",
            "valid SQL",
            "specific query",
        ]
        if any(k in ans for k in refusal_keywords):
            return self._generate_fallback_report(question, data)

        cleaned_ans = self.sanitize_text(ans)

        if not cleaned_ans:
            return self._generate_fallback_report(question, data)

        return cleaned_ans

    def _get_few_shot_examples(self) -> str:
        try:
            path = os.path.join(
                os.path.dirname(__file__), "../../../data/examples.json",
            )
            if os.path.exists(path):
                with open(path) as f:
                    examples = json.load(f)
                return "\n".join([f"Q: {e['q']}\nSQL: {e['sql']}" for e in examples])
        except:
            pass
        return ""

    def generate_sql(self, question: str, history: list = []) -> str | None:
        # Cache Check
        cache_key = f"{question.strip().lower()}|{len(history)}"
        if cache_key in SQLBotClient._sql_cache:
            return SQLBotClient._sql_cache[cache_key]

        history_text = ""
        if history:
            history_text = (
                "Conversation History:\n"
                + "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])
                + "\n"
            )

        schema_context = f"""
Table: open_digger_metrics
Columns:
- repo_name (VARCHAR): Full GitHub repository name (e.g. 'vuejs/core', 'facebook/react')
- metric_type (VARCHAR): Metric being measured. Valid values: {', '.join(settings.SUPPORTED_METRICS)}
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

Supported Repositories: {", ".join(self.repo_list)}

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


def sqlbot_text_to_sql(text: str) -> str | None:
    return SQLBotClient().generate_sql(text)
