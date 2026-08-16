from typing import List, Optional
from pydantic import BaseModel, Field


class AutopilotConfig(BaseModel):
    enabled: bool = False
    max_trade_allocation_pct: float = Field(10.0, ge=1.0, le=50.0)
    stop_loss_pct: float = Field(5.0, ge=1.0, le=25.0)
    take_profit_pct: float = Field(12.0, ge=2.0, le=50.0)
    min_confidence_threshold: float = Field(0.65, ge=0.5, le=0.95)


class AutopilotAction(BaseModel):
    action_type: str
    symbol: str
    quantity: float
    price: float
    reason: str
    timestamp: int


class AutopilotStatusResponse(BaseModel):
    config: AutopilotConfig
    active: bool
    recent_actions: List[AutopilotAction]
    last_evaluated_at: int
