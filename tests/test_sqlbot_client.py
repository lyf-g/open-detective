import pytest
from unittest.mock import MagicMock, patch
from src.backend.services.sqlbot_client import SQLBotClient

def test_extract_sql_markdown():
    client = SQLBotClient()
    raw = "Here is the query: 
```sql
SELECT * FROM table
```"
    assert client._extract_sql(raw) == "SELECT * FROM table"

def test_extract_sql_no_markdown():
    client = SQLBotClient()
    raw = "SELECT * FROM table"
    assert client._extract_sql(raw) == "SELECT * FROM table"

@patch("requests.post")
def test_generate_sql_success(mock_post):
    # Setup mock
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"sql": "SELECT 1"}
    mock_post.return_value = mock_resp
    
    client = SQLBotClient()
    client.api_key = "test_key"
    result = client.generate_sql("test question")
    
    assert result == "SELECT 1"
    mock_post.assert_called_once()

@patch("requests.post")
def test_generate_sql_failure(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_post.return_value = mock_resp
    
    client = SQLBotClient()
    client.api_key = "test_key"
    result = client.generate_sql("broken")
    
    assert result is None

