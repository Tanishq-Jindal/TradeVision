import re
from typing import Optional
from pydantic import BaseModel, Field


class CommandParseRequest(BaseModel):
    command: str = Field(..., description="Natural language command (e.g. 'Buy 20 shares of NVDA')")


class CommandParseResponse(BaseModel):
    raw_command: str
    action: str = Field(..., description="TRADE_BUY, TRADE_SELL, ADD_WATCHLIST, NAVIGATE_SYMBOL, RUN_BACKTEST, VIEW_RISK, UNKNOWN")
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    estimated_price: Optional[float] = None
    estimated_total: Optional[float] = None
    requires_confirmation: bool = False
    preview_message: str
