from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class QuoteResponse(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g. NVDA, AAPL)")
    company: str = Field("", description="Company name")
    name: str = Field("", description="Company name alias")
    current_price: float = Field(0.0, description="Current market price")
    previous_close: float = Field(0.0, description="Previous close price")
    change: float = Field(0.0, description="Price change ($)")
    change_percent: float = Field(0.0, description="Price change percent (%)")
    volume: int = Field(0, description="Daily trading volume")
    high: float = Field(0.0, description="High price of the day")
    low: float = Field(0.0, description="Low price of the day")
    open: float = Field(0.0, description="Open price of the day")
    timestamp: int = Field(0, description="UNIX timestamp in seconds")
    simulated: bool = Field(False, description="Flag indicating if the quote is simulated")
    provider: str = Field("Real-Time Market Feed", description="Market data provider")
    market_status: str = Field("Live", description="Market session status: Live, Closed, After-Hours, or Delayed")
    source: str = Field("Live Exchange Feed", description="Data source description")

    # Short aliases
    c: float = Field(0.0, description="Current price alias")
    d: float = Field(0.0, description="Change alias")
    dp: float = Field(0.0, description="Change percent alias")
    h: float = Field(0.0, description="High alias")
    l: float = Field(0.0, description="Low alias")
    o: float = Field(0.0, description="Open alias")
    pc: float = Field(0.0, description="Previous close alias")
    t: int = Field(0, description="Timestamp alias")

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            c_val = data.get("current_price") if data.get("current_price") is not None else data.get("c", 0.0)
            data["current_price"] = float(c_val)
            data["c"] = float(c_val)

            d_val = data.get("change") if data.get("change") is not None else data.get("d", 0.0)
            data["change"] = float(d_val)
            data["d"] = float(d_val)

            dp_val = data.get("change_percent") if data.get("change_percent") is not None else data.get("dp", 0.0)
            data["change_percent"] = float(dp_val)
            data["dp"] = float(dp_val)

            h_val = data.get("high") if data.get("high") is not None else data.get("h", c_val)
            data["high"] = float(h_val)
            data["h"] = float(h_val)

            l_val = data.get("low") if data.get("low") is not None else data.get("l", c_val)
            data["low"] = float(l_val)
            data["l"] = float(l_val)

            o_val = data.get("open") if data.get("open") is not None else data.get("o", c_val)
            data["open"] = float(o_val)
            data["o"] = float(o_val)

            pc_val = data.get("previous_close") if data.get("previous_close") is not None else data.get("pc", c_val)
            data["previous_close"] = float(pc_val)
            data["pc"] = float(pc_val)

            t_val = data.get("timestamp") if data.get("timestamp") is not None else data.get("t", 0)
            data["timestamp"] = int(t_val)
            data["t"] = int(t_val)

            name_val = data.get("company") or data.get("name") or data.get("symbol") or ""
            data["company"] = str(name_val)
            data["name"] = str(name_val)

        return data


class SymbolSearchResult(BaseModel):
    symbol: str
    description: str
    type: str = "Common Stock"
    currency: str = "USD"
    sector: Optional[str] = None


class CandleBar(BaseModel):
    time: int = Field(..., description="Bar timestamp in seconds")
    open: float
    high: float
    low: float
    close: float
    volume: int


class OHLCVResponse(BaseModel):
    symbol: str
    timeframe: str = "1D"
    candles: List[CandleBar]
    simulated: bool = False
    provider: str = "Real-Time Market Feed"
    market_status: str = "Live"
    source: str = "Live Exchange Feed"


class NewsArticle(BaseModel):
    id: str
    headline: str
    summary: str
    source: str
    url: str
    datetime: int
    symbol: str


class MoverItem(BaseModel):
    rank: int
    symbol: str
    company: str
    price: float
    change: float
    change_percent: float
    market_status: str = "Live"


class MarketMoversResponse(BaseModel):
    gainers: List[MoverItem]
    losers: List[MoverItem]
    updated_at: int
    market_status: str = "Live"
    source: str = "Real Market Data Feed"
    simulated: bool = False


class MarketIndexItem(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    market_status: str = "Live"
    etf_proxy: Optional[str] = None


class MarketPulseResponse(BaseModel):
    indices: List[MarketIndexItem]
    updated_at: int
    market_status: str = "Live"
    source: str = "Real Market Data Feed"
    simulated: bool = False
