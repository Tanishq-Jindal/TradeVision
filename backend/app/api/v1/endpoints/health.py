from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.services.health import get_system_health

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service and dependencies health check",
    description="Verifies the operational status and latency of the backend process, database, and Redis cache.",
)
async def health_check() -> HealthResponse:
    return await get_system_health()
