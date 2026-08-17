from typing import Any, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "TradeVision"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database (Defaults to asyncpg driver for asynchronous SQLAlchemy engine)
    DATABASE_URL: str = "postgresql+asyncpg://tradewise:tradewise123@localhost:5432/tradewise"

    # Redis (Optional distributed cache; defaults to None if not configured)
    REDIS_URL: Optional[str] = None

    # Security
    JWT_SECRET: str = "super-secret-tradewise-jwt-development-key-32chars"
    JWT_EXPIRY_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://[::1]:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # External APIs (Optional for early sprints)
    FINNHUB_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""

    @field_validator("APP_NAME", mode="before")
    @classmethod
    def validate_app_name(cls, v: Union[str, Any]) -> str:
        """Ensures APP_NAME is always non-empty and defaults safely to 'TradeVision'."""
        if not v or not isinstance(v, str) or not v.strip():
            return "TradeVision"
        return v.strip()

    @field_validator("APP_VERSION", mode="before")
    @classmethod
    def validate_app_version(cls, v: Union[str, Any]) -> str:
        """Ensures APP_VERSION defaults safely to '1.0.0'."""
        if not v or not isinstance(v, str) or not v.strip():
            return "1.0.0"
        return v.strip()

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: Union[str, Any]) -> Optional[str]:
        """Normalizes REDIS_URL or returns None if omitted or disabled."""
        if not v or not isinstance(v, str) or not v.strip():
            return None
        url = v.strip()
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1].strip()
        if url.lower() in ("none", "disabled", "false", "off", "null", "not_configured", ""):
            return None
        return url

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Union[str, Any]) -> str:
        """
        Normalizes database URLs to ensure asyncpg is used for PostgreSQL connections.
        Handles Render / cloud PostgreSQL URLs starting with 'postgres://' or 'postgresql://'.
        """
        if not v or not isinstance(v, str):
            return str(v) if v else ""
        url = v.strip()
        # Strip surrounding quotes if configured with quotes in environment variables
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1].strip()

        # Normalize postgres / postgresql schemes to postgresql+asyncpg
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        elif url.startswith("postgresql+psycopg2://"):
            url = "postgresql+asyncpg://" + url[len("postgresql+psycopg2://"):]
        elif url.startswith("sqlite://"):
            url = "sqlite+aiosqlite://" + url[len("sqlite://"):]

        return url

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
