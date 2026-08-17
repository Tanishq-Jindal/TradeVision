import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.core.errors import TradeVisionException, InsufficientFundsError, NotFoundError


@pytest.mark.asyncio
async def test_root_health_endpoint_structure(async_client: AsyncClient):
    """Verify GET /health returns expected schema and fields."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "redis" in data
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/health returns consistent status with root health."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert data["status"] in ["ok", "degraded", "unhealthy"]


@pytest.mark.asyncio
async def test_health_service_degradation_handling(async_client: AsyncClient):
    """Verify health endpoint gracefully degrades if Redis or DB is unreachable."""
    with patch("app.services.health.check_redis_health") as mock_redis_health:
        mock_redis_health.return_value = (False, "unhealthy: connection refused", 1.5)

        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["degraded", "unhealthy"]
        assert data["services"]["redis"]["status"] == "unhealthy"
        assert "unhealthy" in data["redis"]


@pytest.mark.asyncio
async def test_health_service_redis_disabled(async_client: AsyncClient):
    """Verify health endpoint reports Redis as disabled and overall status as ok when REDIS_URL is None."""
    with patch("app.services.health.settings.REDIS_URL", None):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] == "ok"
        assert data["redis"] == "disabled"
        assert data["services"]["redis"]["status"] == "disabled"
        assert data["services"]["redis"]["error"] is None


@pytest.mark.asyncio
async def test_custom_exception_error_envelope(async_client: AsyncClient):
    """Verify custom TradeVisionException returns the standard error envelope."""
    # Temporarily mount a test route raising InsufficientFundsError
    from app.main import app

    @app.get("/test-insufficient-funds")
    async def mock_insufficient_funds():
        raise InsufficientFundsError("Not enough cash to complete this trade.", details={"required": 5000, "available": 1000})

    response = await async_client.get("/test-insufficient-funds")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INSUFFICIENT_CASH"
    assert data["error"]["message"] == "Not enough cash to complete this trade."
    assert data["error"]["details"]["required"] == 5000


@pytest.mark.asyncio
async def test_not_found_error_envelope(async_client: AsyncClient):
    """Verify 404 errors use standard error envelope."""
    response = await async_client.get("/api/v1/non-existent-route")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]


@pytest.mark.asyncio
async def test_request_id_propagation(async_client: AsyncClient):
    """Verify X-Request-ID header is echoed back when provided by client."""
    custom_id = "test-custom-request-id-12345"
    response = await async_client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
