import os
import mysql.connector
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.backend.services.logger import logger

def get_db_connection():
    logger.warning("Using synchronous DB connection (Deprecated). Prefer app.state.pool.")
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "open_detective")
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open MySQL connection with retries
    max_retries = 5
    retry_delay = 5
    
    conn = None
    for i in range(max_retries):
        try:
            logger.info("Attempting to connect to MySQL", attempt=i+1, max_retries=max_retries)
            conn = get_db_connection()
            if conn.is_connected():
                logger.info("Successfully connected to MySQL.")
                app.state.db = conn
                break
        except Exception as e:
            logger.warning("MySQL not ready yet", error=str(e))
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Backend shutting down.")
                raise e
    
    yield
    # Shutdown: Close DB connection
    if conn and conn.is_connected():
        app.state.db.close()
