from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str

    # Redis
    redis_url: str

    # API Authentication
    api_secret_token: str

    # Telegram API
    telegram_api_id: str
    telegram_api_hash: str
    telegram_session_name: str = "ai_news_parser"

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # AI (для будущих этапов)
    openrouter_api_key: Optional[str] = None

    # --- QDRANT SETTINGS ---
    qdrant_url: str
    qdrant_api_key: Optional[str]
    qdrant_collection_name: str

    # App Settings
    environment: str = "development"
    log_level: str = "INFO"

    # Parsing Settings
    telegram_channels: List[str] = [
        "@bbbreaking",
        # "@rybar",
        # "@breakingmash",
        # "@rbc_news"
    ]
    parse_interval_minutes: int = 30
    parse_overlap_hours: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
