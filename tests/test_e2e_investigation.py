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
    Simulate: Question -> SQLBot -> execution against in-memory DB.
    """
    # 1. Mock SQLBot response
    mock_sql = "SELECT value FROM open_digger_metrics WHERE repo_name='vuejs/core' AND metric_type='stars' LIMIT 1"
    mock_gen.return_value = mock_sql
    
    # 2. Get client
    client = SQLBotClient()
    generated_sql = client.generate_sql("how many stars does vue have?")
    assert generated_sql == mock_sql
    
    # 3. Execution against in-memory DB
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    # Create table (Simplified schema for test)
    cursor.execute("CREATE TABLE open_digger_metrics (repo_name TEXT, metric_type TEXT, month TEXT, value REAL)")
    cursor.execute("INSERT INTO open_digger_metrics VALUES ('vuejs/core', 'stars', '2023-01', 100.0)")
    conn.commit()
    
    cursor.execute(generated_sql)
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 100.0
    conn.close()