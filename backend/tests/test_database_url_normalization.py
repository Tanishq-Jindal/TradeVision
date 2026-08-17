import os
import pytest
from app.core.config import Settings
from app.db.session import _normalize_db_url
from sqlalchemy.ext.asyncio import create_async_engine


def test_database_url_render_postgres_scheme_normalization():
    """Verify raw Render postgres:// connection strings are converted to postgresql+asyncpg://."""
    render_url = "postgres://render_user:secret_pass@dpg-abcdefghij-a.oregon-postgres.render.com:5432/tradevision_db"
    settings_obj = Settings(DATABASE_URL=render_url)
    assert settings_obj.DATABASE_URL.startswith("postgresql+asyncpg://")

    engine = create_async_engine(settings_obj.DATABASE_URL)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"


def test_database_url_postgresql_scheme_normalization():
    """Verify standard postgresql:// connection strings without driver use asyncpg, not psycopg2."""
    pg_url = "postgresql://render_user:secret_pass@dpg-abcdefghij-a.oregon-postgres.render.com:5432/tradevision_db"
    settings_obj = Settings(DATABASE_URL=pg_url)
    assert settings_obj.DATABASE_URL.startswith("postgresql+asyncpg://")

    engine = create_async_engine(settings_obj.DATABASE_URL)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"


def test_database_url_psycopg2_scheme_normalization():
    """Verify explicit postgresql+psycopg2:// connection strings are coerced to postgresql+asyncpg://."""
    psycopg_url = "postgresql+psycopg2://render_user:secret_pass@dpg-abcdefghij-a.oregon-postgres.render.com:5432/tradevision_db"
    settings_obj = Settings(DATABASE_URL=psycopg_url)
    assert settings_obj.DATABASE_URL.startswith("postgresql+asyncpg://")

    engine = create_async_engine(settings_obj.DATABASE_URL)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"


def test_database_url_with_sslmode_query():
    """Verify Render URLs with ?sslmode=require parse into asyncpg engine without psycopg2."""
    ssl_url = "postgres://render_user:secret_pass@dpg-abcdefghij-a.oregon-postgres.render.com:5432/tradevision_db?sslmode=require"
    settings_obj = Settings(DATABASE_URL=ssl_url)
    assert settings_obj.DATABASE_URL.startswith("postgresql+asyncpg://")

    engine = create_async_engine(settings_obj.DATABASE_URL)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"


def test_database_url_sqlite_normalization():
    """Verify sqlite:// URLs are coerced to sqlite+aiosqlite:// for async engine."""
    sqlite_url = "sqlite:///:memory:"
    settings_obj = Settings(DATABASE_URL=sqlite_url)
    assert settings_obj.DATABASE_URL == "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(settings_obj.DATABASE_URL)
    assert engine.dialect.name == "sqlite"
    assert engine.dialect.driver == "aiosqlite"


def test_session_normalize_helper():
    """Verify defensive helper in session.py normalizes all database schemes."""
    assert _normalize_db_url("postgres://user:pass@host/db") == "postgresql+asyncpg://user:pass@host/db"
    assert _normalize_db_url("postgresql://user:pass@host/db") == "postgresql+asyncpg://user:pass@host/db"
    assert _normalize_db_url("postgresql+psycopg2://user:pass@host/db") == "postgresql+asyncpg://user:pass@host/db"
    assert _normalize_db_url("postgresql+asyncpg://user:pass@host/db") == "postgresql+asyncpg://user:pass@host/db"
    assert _normalize_db_url("sqlite:///:memory:") == "sqlite+aiosqlite:///:memory:"


def test_app_name_empty_fallback():
    """Verify empty or whitespace APP_NAME safely defaults to TradeVision to prevent FastAPI OpenAPI AssertionError."""
    from fastapi import FastAPI

    empty_settings = Settings(APP_NAME="", APP_VERSION="")
    assert empty_settings.APP_NAME == "TradeVision"
    assert empty_settings.APP_VERSION == "1.0.0"

    whitespace_settings = Settings(APP_NAME="   ")
    assert whitespace_settings.APP_NAME == "TradeVision"

    # Verify FastAPI initialization does not raise AssertionError: A title must be provided for OpenAPI
    app = FastAPI(title=empty_settings.APP_NAME or "TradeVision")
    assert app.title == "TradeVision"

