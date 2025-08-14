from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str

    # Redis
    redis_url: str

    # API Authentication
    api_secret_token: str

    # AI (для будущих этапов)
    openrouter_api_key: Optional[str] = None

    # App Settings
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()