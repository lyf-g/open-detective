import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from src.backend.main import app

# 1. Async Context Manager Helper
class AsyncContextManager:
    def __init__(self, return_value=None):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# 2. Mock Cursor
mock_cursor = MagicMock()
mock_cursor.execute = AsyncMock()
mock_cursor.fetchall = AsyncMock(return_value=[])
mock_cursor.fetchone = AsyncMock(return_value={"count": 0})

# 3. Mock Connection
mock_conn = MagicMock()
mock_conn.cursor = MagicMock(return_value=AsyncContextManager(mock_cursor))
mock_conn.commit = AsyncMock()
mock_conn.ping = AsyncMock()

# 4. Mock Pool
mock_pool = MagicMock()
mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

# Inject into app state
app.state.pool = mock_pool

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_session():
    response = client.post("/api/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "New Investigation"

def test_chat_stream_flow():
    # Setup fetchone for user message count check
    mock_cursor.fetchone.return_value = {"count": 0}
    
    session_res = client.post("/api/v1/sessions")
    session_id = session_res.json()["id"]
    
    response = client.post("/api/v1/chat/stream", json={"message": "vue stars", "session_id": session_id})
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    
    lines = response.text.strip().split('\n')
    assert len(lines) >= 1
    
    meta = json.loads(lines[0])
    assert meta["type"] == "meta"

def test_list_sessions():
    mock_cursor.fetchall.return_value = [
        {"id": "1", "title": "Test", "created_at": "2023-01-01"}
    ]
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test"
