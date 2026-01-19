# Copyright (c) 2026 Open-Detective Contributors
# Licensed under the MIT License. See LICENSE file for details.

import asyncio
import json
import subprocess
import sys
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiomysql
from apscheduler.schedulers.background import BackgroundScheduler
from asgi_correlation_id import CorrelationIdMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.backend.api.v1.api import api_router
from src.backend.core.config import settings
from src.backend.core.limiter import limiter
from src.backend.schemas.common import BaseError
from src.backend.services.logger import configure_logger, logger

load_dotenv()

MAX_RETRIES = 5
ETL_INTERVAL_HOURS = 24


def ensure_system_integrity() -> None:
    """Ensure critical configuration files exist."""
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data"
    repo_path = data_dir / "repos.json"

    data_dir.mkdir(parents=True, exist_ok=True)
    if not repo_path.exists():
        logger.warning("repos.json not found. Creating default configuration.")
        try:
            with repo_path.open("w") as f:
                json.dump(["vuejs/core", "facebook/react", "fastapi/fastapi"], f, indent=2)
        except Exception as e:
            logger.error("failed_to_create_default_repos_config", error=str(e))


def run_sqlbot_init() -> None:
    """Run the SQLBot auto-configuration script."""
    script_path = (Path(__file__).parent.parent.parent / "data" / "etl_scripts" / "init_sqlbot.py").resolve()
    try:
        logger.info("Starting SQLBot auto-configuration...")
        subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("SQLBot auto-configuration finished.")
    except Exception as e:
        logger.warning(f"SQLBot auto-config failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    start_time = time.time()
    configure_logger()
    logger.info("System initializing", python_path=sys.path)
    ensure_system_integrity()

    # Trigger SQLBot Init in background
    asyncio.create_task(asyncio.to_thread(run_sqlbot_init))

    # Lazy import ETL script to avoid sys.path issues during startup
    scheduler = None
    try:
        root_dir = Path(__file__).parent.parent.parent.resolve()
        sys.path.append(str(root_dir))
        from data.etl_scripts.fetch_opendigger import run_etl

        scheduler = BackgroundScheduler()
        scheduler.add_job(run_etl, "interval", hours=ETL_INTERVAL_HOURS)
        scheduler.start()
    except ImportError:
        logger.warning("ETL Script import failed, scheduler not started")

    # Async Pool
    pool: aiomysql.Pool | None = None
    for i in range(MAX_RETRIES):
        try:
            logger.info("Connecting to MySQL (Async)", attempt=i + 1)
            pool = await aiomysql.create_pool(
                host=settings.DB_HOST,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD.get_secret_value(),
                db=settings.DB_NAME,
                autocommit=True,
                cursorclass=aiomysql.DictCursor,
                minsize=settings.DB_POOL_MIN,
                maxsize=settings.DB_POOL_MAX,
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
        sys.exit(1)

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
        "url": "https://github.com/lyf-g/open-detective",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CorrelationIdMiddleware)


# Process Time Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any) -> Any:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any) -> Any:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        content=BaseError(code=exc.status_code, message=exc.detail).model_dump(),
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error("Global Exception", error=str(exc))
    return JSONResponse(
        content=BaseError(
            code=500, message="Internal Server Error", details=str(exc),
        ).model_dump(),
        status_code=500,
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["System"], summary="System Root", response_description="Basic system information.")
def read_root() -> dict[str, str]:
    return {
        "system": "Open-Detective",
        "status": "operational",
        "version": "1.0.0",
        "motto": "Don't just query. Investigate.",
    }