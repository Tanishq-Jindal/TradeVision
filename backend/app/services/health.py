import logging
import time
from datetime import datetime, timezone
import redis.asyncio as aioredis
from app.core.config import settings
from app.db.session import check_db_health
from app.schemas.health import HealthResponse, ServiceHealth

logger = logging.getLogger(__name__)


async def check_redis_health() -> tuple[bool, str, float]:
    """
    Performs a real Redis ping health check if REDIS_URL is configured.
    Returns: (is_healthy, status_message, latency_ms)
    """
    if not settings.REDIS_URL:
        return True, "disabled", 0.0

    start_time = time.perf_counter()
    client = None
    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
        pong = await client.ping()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if pong:
            return True, "ok", latency_ms
        return False, "unhealthy: no response", latency_ms
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning(f"Redis health check failed: {str(e)}")
        return False, f"unhealthy: {str(e)}", latency_ms
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


async def get_system_health() -> HealthResponse:
    """
    Runs health checks across all backend dependencies.
    """
    db_healthy, db_status, db_latency = await check_db_health()
    redis_healthy, redis_status, redis_latency = await check_redis_health()

    # Determine overall status:
    # Database is critical; Redis is optional.
    # If DB is healthy and Redis is healthy/disabled -> "ok"
    # If DB is healthy but Redis is configured and failing -> "degraded"
    # If DB is unhealthy -> "unhealthy"
    if db_healthy:
        if redis_healthy:
            overall_status = "ok"
        else:
            overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    redis_display = "disabled" if redis_status == "disabled" else ("ok" if redis_healthy else redis_status)
    redis_service_status = "disabled" if redis_status == "disabled" else ("ok" if redis_healthy else "unhealthy")

    return HealthResponse(
        status=overall_status,
        db="ok" if db_healthy else db_status,
        redis=redis_display,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services={
            "database": ServiceHealth(
                status="ok" if db_healthy else "unhealthy",
                latency_ms=db_latency,
                error=None if db_healthy else db_status,
            ),
            "redis": ServiceHealth(
                status=redis_service_status,
                latency_ms=redis_latency,
                error=None if redis_healthy else redis_status,
            ),
        },
    )
