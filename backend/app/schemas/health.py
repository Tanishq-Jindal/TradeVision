from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    status: str = Field(..., description="'ok' or 'unhealthy'")
    latency_ms: Optional[float] = Field(None, description="Check round-trip time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status: 'ok', 'degraded', or 'unhealthy'")
    db: str = Field(..., description="Database status ('ok' or error summary)")
    redis: str = Field(..., description="Redis status ('ok' or error summary)")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    services: Dict[str, ServiceHealth] = Field(..., description="Per-service detailed health info")
