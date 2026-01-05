import os
from src.backend.services.sql_engine import mock_text_to_sql
from src.backend.services.sqlbot_client import SQLBotClient

def get_sql_engine():
    """
    Factory function to return the configured SQL engine.
    """
    engine_type = os.getenv("SQL_ENGINE_TYPE", "mock").lower()
    
    if engine_type == "sqlbot":
        client = SQLBotClient(
            endpoint=os.getenv("SQLBOT_ENDPOINT", "http://localhost:8080")
        )
        return client.generate_sql
    
    # Default to mock
    return mock_text_to_sql
