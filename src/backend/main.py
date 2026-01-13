# Copyright (c) 2026 Open-Detective Contributors
# Licensed under the MIT License. See LICENSE file for details.

import os
import aiomysql
import json
import sys
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.backend.services.logger import configure_logger, logger
from src.backend.api.v1.api import api_router
from src.backend.core.limiter import limiter
from src.backend.core.config import settings

import subprocess

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

def run_sqlbot_init():
    """Runs the SQLBot auto-configuration script."""
    # /app/src/backend/main.py -> /app/data/...
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/etl_scripts/init_sqlbot.py'))
    try:
        logger.info("Starting SQLBot auto-configuration...")
        subprocess.run([sys.executable, script_path], check=True)
        logger.info("SQLBot auto-configuration finished.")
    except Exception as e:
        logger.warning(f"SQLBot auto-config failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_time = time.time()
    configure_logger()
    check_system_integrity()

    # Trigger SQLBot Init in background
    asyncio.create_task(asyncio.to_thread(run_sqlbot_init))

    # Lazy import ETL script to avoid sys.path issues during startup
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
        from data.etl_scripts.fetch_opendigger import run_etl
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_etl, 'interval', hours=24)
        scheduler.start()
    except ImportError:
        logger.warning("ETL Script import failed, scheduler not started")
        scheduler = None

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
                cursorclass=aiomysql.DictCursor,
                minsize=settings.DB_POOL_MIN,
                maxsize=settings.DB_POOL_MAX
            )
            app.state.pool = pool
            logger.info("Connected to MySQL.")
            break
        except Exception as e:
            logger.warning("MySQL connection failed", error=str(e))
            if i < max_retries - 1:
                await asyncio.sleep(5)
    
    if not pool:
        logger.critical("Could not connect to MySQL after multiple attempts. Exiting.")
        raise RuntimeError("Database connection failed")

    duration = time.time() - start_time
    logger.info(f"Startup complete in {duration:.2f}s")

    yield
    if scheduler:
        scheduler.shutdown()
    if pool:
        pool.close()
        await pool.wait_closed()

app = FastAPI(
    title="Open-Detective API",
    description="""
    ## 🕵️‍♂️ Open-Detective: The Autonomous Open Source Insight Engine

    **Key Capabilities:**
    - **Natural Language Inquiry**: Chat with your data using SQLBot.
    - **Neural Deduction**: Automated insights and anomaly detection.
    - **Root Cause Analysis**: Bayesian inference for event correlation.
    
    Powered by FastAPI, AsyncIO, and OpenDigger.
    """,
    version="1.0.0",
    contact={
        "name": "Open-Detective Team",
        "url": "https://github.com/lyf-g/open-detective"
    },
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8082", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CorrelationIdMiddleware)

# Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)

from src.backend.schemas.common import BaseError

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        content=BaseError(code=exc.status_code, message=exc.detail).model_dump(),
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global Exception", error=str(exc))
    return JSONResponse(
        content=BaseError(code=500, message="Internal Server Error", details=str(exc)).model_dump(),
        status_code=500
    )

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["System"])
def read_root():
    return {
        "system": "Open-Detective",
        "status": "operational",
        "version": "1.0.0",
        "motto": "Don't just query. Investigate."
    }
