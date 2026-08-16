from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BacktestTrade(BaseModel):
    symbol: str
    entry_time: int
    exit_time: int
    side: str = "BUY"
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    pnl_pct: float


class EquityPoint(BaseModel):
    time: int
    equity: float


class BacktestRequest(BaseModel):
    symbol: str = "NVDA"
    strategy_prompt: Optional[str] = None
    strategy_type: str = "RSI_MOMENTUM"  # RSI_MOMENTUM, SMA_CROSSOVER, MACD_MOMENTUM, BUY_AND_HOLD
    initial_cash: float = 100000.0
    timeframe: str = "1D"
    bars_count: int = 150
    params: Dict[str, float] = Field(default_factory=dict)


class BacktestResult(BaseModel):
    symbol: str
    strategy_name: str
    initial_cash: float
    final_equity: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    equity_curve: List[EquityPoint]
    trades: List[BacktestTrade]
