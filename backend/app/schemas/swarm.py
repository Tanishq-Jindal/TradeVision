from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentOpinion(BaseModel):
    agent_name: str
    role: str
    signal: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    recommended_weight: float


class SwarmConsensusResponse(BaseModel):
    symbol: str
    consensus_signal: str = Field(..., description="STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL")
    consensus_score: float = Field(..., ge=-1.0, le=1.0)
    agreement_percentage: float = Field(..., ge=0.0, le=100.0)
    max_position_size_pct: float = Field(..., description="Risk-adjusted max allocation % of portfolio")
    summary: str
    agents: List[AgentOpinion]
    timestamp: int
