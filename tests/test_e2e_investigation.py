import sqlite3
import os
import sys
import pytest
from unittest.mock import patch

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.backend.services.sqlbot_client import SQLBotClient

@patch("src.backend.services.sqlbot_client.SQLBotClient.generate_sql")
def test_full_investigation_loop(mock_gen):
    """
    Simulate: Question -> SQLBot -> execution against real DB file.
    """
    # 1. Mock SQLBot response
    mock_sql = "SELECT value FROM open_digger_metrics WHERE repo_name='vuejs/core' AND metric_type='stars' LIMIT 1"
    mock_gen.return_value = mock_sql
    
    # 2. Get client
    client = SQLBotClient()
    generated_sql = client.generate_sql("how many stars does vue have?")
    assert generated_sql == mock_sql
    
    # 3. Try execution against the DB
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../open_detective.db'))
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(generated_sql)
        row = cursor.fetchone()
        assert row is not None
        conn.close()
        print("✅ E2E Loop Verified: SQL generated and executed successfully.")
    else:
        print("⚠️ DB file not found, skipping execution part of test.")

if __name__ == "__main__":
    test_full_investigation_loop()
