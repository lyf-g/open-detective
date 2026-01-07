import os
import mysql.connector
import time
import json
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.backend.services.logger import configure_logger, logger
from src.backend.api.v1.api import api_router
from src.backend.core.limiter import limiter

# Allow importing from data directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
try:
    from data.etl_scripts.fetch_opendigger import run_etl
except ImportError:
    run_etl = lambda: print("ETL Script import failed")

load_dotenv()

def check_system_integrity():
    """Ensures critical configuration files exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    repo_path = os.path.join(data_dir, 'repos.json')
    if not os.path.exists(repo_path):
        logger.warning("repos.json not found. Creating default configuration.")
        with open(repo_path, 'w') as f:
            json.dump(["vuejs/core", "facebook/react", "fastapi/fastapi"], f, indent=2)
    env_path = os.path.join(base_dir, '.env')
    if not os.path.exists(env_path):
        logger.warning(".env not found. Please configure your environment variables.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    check_system_integrity()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_etl, 'interval', hours=24)
    scheduler.start()

    max_retries = 5
    conn = None
    for i in range(max_retries):
        try:
            logger.info("Attempting to connect to MySQL", attempt=i+1, max_retries=max_retries)
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "open_detective")
            )
            if conn.is_connected():
                logger.info("Successfully connected to MySQL.")
                app.state.db = conn
                break
        except Exception as e:
            logger.warning("MySQL not ready yet", error=str(e))
            if i < max_retries - 1:
                time.sleep(5)
            else:
                logger.error("Max retries reached. Backend shutting down.")
                raise e
    
    yield
    scheduler.shutdown()
    if conn and conn.is_connected():
        app.state.db.close()

app = FastAPI(
    title="Open-Detective API",
    description="Backend for Open-Detective",
    version="0.1.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Open-Detective Backend is running!"}