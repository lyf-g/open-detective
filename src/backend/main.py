import os
import aiomysql
import time
import json
import sys
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.backend.services.logger import configure_logger, logger
from src.backend.api.v1.api import api_router
from src.backend.core.limiter import limiter
from src.backend.core.config import settings

# Allow importing from data directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
try:
    from data.etl_scripts.fetch_opendigger import run_etl
except ImportError:
    run_etl = lambda: print("ETL Script import failed")

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    check_system_integrity()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_etl, 'interval', hours=24)
    scheduler.start()

    # Async Pool
    pool = None
    max_retries = 5
    for i in range(max_retries):
        try:
            logger.info("Connecting to MySQL (Async)", attempt=i+1)
            pool = await aiomysql.create_pool(
                host=settings.DB_HOST,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                db=settings.DB_NAME,
                autocommit=True,
                cursorclass=aiomysql.DictCursor
            )
            app.state.pool = pool
            logger.info("Connected to MySQL.")
            break
        except Exception as e:
            logger.warning("MySQL connection failed", error=str(e))
            if i < max_retries - 1:
                await asyncio.sleep(5)
    
    yield
    scheduler.shutdown()
    if pool:
        pool.close()
        await pool.wait_closed()

app = FastAPI(
    title="Open-Detective API",
    description="Backend for Open-Detective",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(CorrelationIdMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Open-Detective Backend is running!"}