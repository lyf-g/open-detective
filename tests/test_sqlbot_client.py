import pytest
from unittest.mock import MagicMock, patch
from src.backend.services.sqlbot_client import SQLBotClient

def test_extract_sql_markdown():
    client = SQLBotClient()
    raw = """Here is the query: 
```sql
SELECT * FROM table
```"""
    assert client._extract_sql(raw) == "SELECT * FROM table"

def test_extract_sql_no_markdown():
    client = SQLBotClient()
    raw = "SELECT * FROM table"
    assert client._extract_sql(raw) == "SELECT * FROM table"

def test_repair_sql_metric_mapping():
    client = SQLBotClient()
    sql = "SELECT * FROM t WHERE metric='star'"
    repaired = client.repair_sql(sql)
    assert "'stars'" in repaired

@patch("requests.post")
@patch("src.backend.services.sqlbot_client.SQLBotClient._login")
def test_generate_sql_success(mock_login, mock_post):
    # Mock login to return a token so it doesn't try to network
    mock_login.return_value = "fake_token"

    # Setup mock for chat/start
    mock_start_resp = MagicMock()
    mock_start_resp.status_code = 200
    mock_start_resp.json.return_value = {"data": {"id": "chat_123"}}
    
    # Setup mock for chat/question (streaming)
    mock_qa_resp = MagicMock()
    mock_qa_resp.status_code = 200
    # Simulate streaming response lines
    mock_qa_resp.iter_lines.return_value = [
        b'data: {"content": "```sql\\nSELECT repo_name, "}',
        b'data: {"content": "month, value FROM "}',
        b'data: {"content": "open_digger_metrics```"}',
        b'data: [DONE]'
    ]
    
    # Configure side_effect for requests.post
    # Note: _ask_ai calls _get_headers -> _login (mocked)
    # Then calls chat/start, then chat/question.
    mock_post.side_effect = [mock_start_resp, mock_qa_resp]
    
    client = SQLBotClient()
    result = client.generate_sql("test question")
    
    assert "SELECT repo_name, month, value FROM open_digger_metrics" in result
    assert mock_post.call_count == 2

@patch("src.backend.services.sqlbot_client.SQLBotClient._ask_ai")
def test_generate_summary_refusal_fallback(mock_ask):
    mock_ask.return_value = "您当前的请求是生成一份纯文本的Markdown分析报告，这超出了我的能力范围。"
    
    client = SQLBotClient()
    data = [{"repo_name": "vuejs/core", "month": "2023-01", "value": 100}]
    
    result = client.generate_summary("Analyze this", data)
    
    # Assert fallback was triggered (checking for unique string in fallback report)
    assert "核心仓库活动分析报告" in result
    assert "数据概览" in result