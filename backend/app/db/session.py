import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)


def _normalize_db_url(url: str) -> str:
    """
    Ensures the database connection URL is formatted with the appropriate async driver scheme.
    """
    if not url:
        return url
    url = url.strip()
    if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
        url = url[1:-1].strip()

    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://"):]
    elif url.startswith("sqlite://"):
        return "sqlite+aiosqlite://" + url[len("sqlite://"):]

    return url


# Resolve normalized async database URL
db_url: str = _normalize_db_url(settings.DATABASE_URL)

# Engine configuration
engine_kwargs: dict = {
    "echo": False,
    "future": True,
}

if "sqlite" not in db_url:
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })

# Initialize AsyncEngine with asyncpg driver
engine: AsyncEngine = create_async_engine(
    db_url,
    **engine_kwargs
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> tuple[bool, str, float]:
    """
    Performs a lightweight DB health check.
    Returns: (is_healthy, status_message, latency_ms)
    """
    import time

    start_time = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return True, "ok", latency_ms
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning(f"Database health check failed: {str(e)}")
        return False, f"unhealthy: {str(e)}", latency_ms
