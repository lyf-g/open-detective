import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from src.backend.main import app

# Mock Async Pool
mock_pool = MagicMock()
mock_conn = AsyncMock()
mock_cursor = AsyncMock()

# Setup async context managers
# pool.acquire() -> conn
mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
# conn.cursor() -> cur
mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

# Setup cursor returns
mock_cursor.fetchone.return_value = {"count": 0}
mock_cursor.fetchall.return_value = []

# Inject mock into app state
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