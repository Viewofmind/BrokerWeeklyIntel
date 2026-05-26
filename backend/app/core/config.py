"""
BrokerWeeklyIntel - Application Configuration
Uses pydantic-settings for clean env var handling.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "BrokerWeeklyIntel"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=True, validation_alias="DEBUG")

    # Data Sources
    twitter_bearer_token: str | None = Field(default=None, validation_alias="TWITTER_BEARER_TOKEN")
    apify_api_token: str | None = Field(default=None, validation_alias="APIFY_API_TOKEN")
    firecrawl_api_key: str | None = Field(default=None, validation_alias="FIRECRAWL_API_KEY")

    # Connector Toggles (opt-in for heavy/external services)
    enable_apify: bool = Field(default=False, validation_alias="ENABLE_APIFY")
    enable_firecrawl: bool = Field(default=False, validation_alias="ENABLE_FIRECRAWL")

    reddit_client_id: str | None = Field(default=None, validation_alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str | None = Field(default=None, validation_alias="REDDIT_CLIENT_SECRET")

    # MiroFish
    mirofish_enabled: bool = Field(default=False, validation_alias="MIROFISH_ENABLED")

    # Storage
    database_url: str = Field(
        default="sqlite:///./backend/data/broker_intel.db",
        validation_alias="DATABASE_URL"
    )

    # Scheduling
    weekly_analysis_day: str = Field(default="Sunday", validation_alias="WEEKLY_ANALYSIS_DAY")
    weekly_analysis_time: str = Field(default="08:30", validation_alias="WEEKLY_ANALYSIS_TIME")
    timezone: str = Field(default="Asia/Kolkata", validation_alias="TIMEZONE")

    # Brokers
    brokers: List[str] = Field(
        default=[
            "Zerodha", "Groww", "Angel One", "Upstox", "Fyers",
            "ICICI Direct", "5Paisa", "Kotak Securities", "HDFC Sky"
        ],
        validation_alias="BROKERS"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias="CORS_ALLOWED_ORIGINS"
    )

    # Report settings
    report_output_dir: str = Field(default="./reports", validation_alias="REPORT_OUTPUT_DIR")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
