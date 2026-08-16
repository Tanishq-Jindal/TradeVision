from fastapi import APIRouter
from app.schemas.swarm import SwarmConsensusResponse
from app.services.swarm import generate_swarm_consensus

router = APIRouter()


@router.get(
    "/{symbol}",
    response_model=SwarmConsensusResponse,
    summary="Get multi-agent consensus deliberation",
    description="Orchestrates 4 specialized financial agents (Momentum, Mean Reversion, Sentiment, Risk) into a unified consensus deliberation.",
)
async def get_swarm(symbol: str) -> SwarmConsensusResponse:
    return await generate_swarm_consensus(symbol)
