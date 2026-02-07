"""Application configuration using Pydantic Settings"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "CheziousBot"
    app_version: str = "1.0.0"
    debug: bool = False

    # Groq API Configuration
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    groq_max_tokens: int = 512
    groq_temperature: float = 0.6

    # Database
    database_url: str = "sqlite+aiosqlite:///./cheziousbot.db"

    # Context Management
    context_window_size: int = 10
    max_message_length: int = 500

    # Rate Limiting
    rate_limit_per_minute: int = 20

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
