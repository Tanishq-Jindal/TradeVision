from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol (e.g. NVDA, AAPL)")
    side: Literal["BUY", "SELL", "buy", "sell"] = Field("BUY", description="Order side: BUY or SELL")
    quantity: int = Field(..., gt=0, description="Positive integer number of shares to trade")
    order_type: Literal["MARKET", "market"] = Field("MARKET", description="Order type: MARKET")
    price: Optional[float] = Field(None, gt=0, description="Optional execution price override")

    @field_validator("symbol", mode="after")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("side", mode="after")
    @classmethod
    def normalize_side(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("order_type", mode="after")
    @classmethod
    def normalize_order_type(cls, v: str) -> str:
        return v.strip().upper()


class TradeOrderRequest(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol (e.g. NVDA, AAPL)")
    quantity: float = Field(..., gt=0, description="Number of shares to buy or sell (must be > 0)")
    price: Optional[float] = Field(None, gt=0, description="Optional execution price override")
    side: Optional[str] = "BUY"
    order_type: Optional[str] = "MARKET"

    @field_validator("symbol", mode="after")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()


class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    portfolio_id: int
    symbol: str
    side: str
    quantity: float
    price: float
    total_value: float
    executed_at: datetime


class PositionDetail(BaseModel):
    id: Optional[int] = None
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    avg_entry_price: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    daily_change_pct: Optional[float] = 0.0
    updated_at: Optional[datetime] = None


class PositionResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    daily_change_pct: float
    updated_at: datetime


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount: float
    balance_after: float
    related_trade_id: Optional[int] = None
    created_at: datetime


class PortfolioResponse(BaseModel):
    cash_balance: float
    total_market_value: float
    total_portfolio_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    positions: List[PositionDetail]


class PortfolioSummaryResponse(BaseModel):
    cash_balance: float
    invested_value: float
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    daily_pnl: float
    daily_pnl_pct: float
    positions_count: int


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    added_at: datetime


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    items: List[WatchlistItemResponse] = []


class WatchlistAddRequest(BaseModel):
    symbol: str = Field(..., description="Symbol to add to watchlist")

    @field_validator("symbol", mode="after")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()
