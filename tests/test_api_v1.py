import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.backend.main import app

# Mock DB Connection globally for tests
mock_conn = MagicMock()
mock_cursor = MagicMock()
mock_conn.cursor.return_value = mock_cursor
mock_conn.is_connected.return_value = True

# Setup cursor returns
mock_cursor.fetchone.return_value = [0] # Default count
mock_cursor.fetchall.return_value = [] # Default empty list

# Inject mock into app state
app.state.db = mock_conn

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
    # 1. Create Session
    session_res = client.post("/api/v1/sessions")
    session_id = session_res.json()["id"]
    
    # 2. Chat Stream
    # Mock ChatService execution to avoid real SQL/LLM calls if possible,
    # but here we are testing the endpoint logic which calls ChatService.
    # Since DB is mocked, SQL execution will return empty list or mock.
    # SQL generation will use Mock Engine (default env) or fail gracefully.
    
    response = client.post("/api/v1/chat/stream", json={"message": "vue stars", "session_id": session_id})
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    
    lines = response.text.strip().split('\n')
    assert len(lines) >= 1
    
    meta = json.loads(lines[0])
    assert meta["type"] == "meta"
    # Should be mock engine by default
    assert "mock" in meta.get("engine_source", "mock")

def test_list_sessions():
    mock_cursor.fetchall.return_value = [
        {"id": "1", "title": "Test", "created_at": "2023-01-01"}
    ]
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test"
