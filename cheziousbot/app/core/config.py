import os
import sys
import types
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Compatibility Shim ───────────────────────────────────────────────────────
try:
    import langchain_core.pydantic_v1
except ImportError:
    try:
        from pydantic import v1 as pydantic_v1
        mod = types.ModuleType("langchain_core.pydantic_v1")
        for attr in dir(pydantic_v1):
            if not attr.startswith("__"):
                setattr(mod, attr, getattr(pydantic_v1, attr))
        sys.modules["langchain_core.pydantic_v1"] = mod
    except ImportError:
        pass

class Settings(BaseSettings):
    # Environment Selection
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # LLM — Primary (Qwen)
    QWEN_API_KEY: str
    QWEN_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen3.5-flash"

    # LLM — Fallback (OpenAI)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Shared LLM params
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024

    # Infrastructure
    REDIS_URL: str = "redis://localhost:6379"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cheziousbot"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_DEFAULT: str = "30 per minute"

    # Thresholds
    SUMMARIZE_TOKEN_THRESHOLD: int = 3000
    RECENT_CONTEXT_MESSAGES: int = 10
    MAX_CONFIRMATION_RETRIES: int = 2
    MAX_EXTRACTION_RETRIES: int = 3
    MAX_LLM_RETRIES: int = 2

    # App
    PROJECT_NAME: str = "CheziousBot API"
    VERSION: str = "1.0.0"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    # Determine which .env to load based on APP_ENV system variable if present
    # Default is still .env
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.getenv('ENVIRONMENT', 'development')}"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
