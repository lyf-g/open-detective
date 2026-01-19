from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    # Database
    DB_HOST: str = "localhost"
    DB_USER: str = "root"
    DB_PASSWORD: SecretStr = SecretStr("")
    DB_NAME: str = "open_detective"
    DB_POOL_MIN: int = 1
    DB_POOL_MAX: int = 20
    REDIS_URL: str = "redis://redis:6379/0"

    # App
    APP_ENV: str = "production"
    SQL_ENGINE_TYPE: str = "mock"
    ANOMALY_THRESHOLD: float = 0.5
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:8082", "*"]
    ALLOWED_REPOS: list[str] = [
        "vuejs/core",
        "facebook/react",
        "fastapi/fastapi",
        "tensorflow/tensorflow",
        "microsoft/vscode",
        "kubernetes/kubernetes",
    ]
    SUPPORTED_METRICS: list[str] = [
        "stars",
        "activity",
        "openrank",
        "bus_factor",
        "issues_new",
        "issues_closed",
    ]

    # SQLBot
    SQLBOT_ENDPOINT: str = "http://sqlbot:8000"
    SQLBOT_USERNAME: str = "admin"
    SQLBOT_PASSWORD: SecretStr = SecretStr("SQLBot@123456")
    SQLBOT_DATASOURCE_ID: int = 1
    SQLBOT_API_KEY: SecretStr = SecretStr("")
    SQLBOT_TIMEOUT: int = 30
    SQLBOT_AI_TIMEOUT: int = 60

    @field_validator("ANOMALY_THRESHOLD")
    @classmethod
    def check_threshold(cls, v: float) -> float:
        if v <= 0 or v > 10.0:
            err_msg = "ANOMALY_THRESHOLD must be between 0 and 10.0"
            raise ValueError(err_msg)
        return v

    @field_validator("DB_POOL_MAX")
    @classmethod
    def check_pool_size(cls, v: int, info: Any) -> int:
        if "DB_POOL_MIN" in info.data and v < info.data["DB_POOL_MIN"]:
            err_msg = "DB_POOL_MAX must be greater than or equal to DB_POOL_MIN"
            raise ValueError(err_msg)
        return v

    def __str__(self) -> str:
        return f"Settings(DB_NAME={self.DB_NAME}, SQL_ENGINE_TYPE={self.SQL_ENGINE_TYPE})"

    def __repr__(self) -> str:
        return self.__str__()

    # Resolves to project root .env if running from src/backend
    # or relies on environment variables already set
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
