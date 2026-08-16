from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.correlation import CorrelationNetworkResponse
from app.services.correlation import generate_correlation_network

router = APIRouter()


@router.get(
    "/network",
    response_model=CorrelationNetworkResponse,
    summary="Get multi-asset correlation network graph",
    description="Returns nodes and weighted correlation links for rendering a force-directed network graph.",
)
async def get_correlation_network(
    symbols: Optional[str] = Query(None, description="Comma-separated stock ticker symbols"),
) -> CorrelationNetworkResponse:
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
    return await generate_correlation_network(sym_list)
