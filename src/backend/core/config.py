from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
import os

class Settings(BaseSettings):
    """
    Application configuration settings.
    """
    # Database
    DB_HOST: str = "localhost"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "open_detective"
    DB_POOL_MIN: int = 1
    DB_POOL_MAX: int = 20
    REDIS_URL: str = "redis://redis:6379/0"
    
    # App
    SQL_ENGINE_TYPE: str = "mock"
    ANOMALY_THRESHOLD: float = 0.5
    
    # SQLBot
    SQLBOT_ENDPOINT: str = "http://sqlbot:8000"
    SQLBOT_USERNAME: str = "admin"
    SQLBOT_PASSWORD: str = "SQLBot@123456"
    SQLBOT_DATASOURCE_ID: int = 1
    SQLBOT_API_KEY: str = ""
    
    @field_validator("ANOMALY_THRESHOLD")
    @classmethod
    def check_threshold(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("ANOMALY_THRESHOLD must be positive")
        return v

    @field_validator("DB_POOL_MAX")
    @classmethod
    def check_pool_size(cls, v: int, info) -> int:
        if "DB_POOL_MIN" in info.data and v < info.data["DB_POOL_MIN"]:
            raise ValueError("DB_POOL_MAX must be greater than or equal to DB_POOL_MIN")
        return v

    # Resolves to project root .env if running from src/backend
    # or relies on environment variables already set
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
