from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.market import (
    NewsArticle,
    OHLCVResponse,
    QuoteResponse,
    SymbolSearchResult,
)
from app.services.market_data import (
    get_news,
    get_ohlcv,
    get_quote,
    quote_event_generator,
    search_symbols,
)

router = APIRouter()


@router.get(
    "/search",
    response_model=List[SymbolSearchResult],
    summary="Search stock symbols",
    description="Autocomplete search by stock ticker symbol, company name, or industry sector.",
)
async def search(
    q: str = Query("", description="Symbol or company name search query"),
) -> List[SymbolSearchResult]:
    sanitized = q.strip()[:50]
    return await search_symbols(sanitized)


@router.get(
    "/quote/{symbol}",
    response_model=QuoteResponse,
    summary="Get real-time stock quote",
    description="Returns latest price tick, day change, high, low, open, previous close, and simulated status with multi-tier caching.",
)
async def quote(
    symbol: str,
    current_user: User = Depends(get_current_user),
) -> QuoteResponse:
    return await get_quote(symbol)


@router.get(
    "/ohlcv/{symbol}",
    response_model=OHLCVResponse,
    summary="Get historical candlestick chart data",
    description="Returns historical open, high, low, close, and volume series.",
)
async def ohlcv(
    symbol: str,
    range: str = Query("1D", description="Candle timeframe / range (e.g. 1D, 1W)"),
    count: int = Query(100, ge=10, le=500, description="Number of bars to return"),
    current_user: User = Depends(get_current_user),
) -> OHLCVResponse:
    return await get_ohlcv(symbol, timeframe=range, count=count)


@router.get(
    "/news/{symbol}",
    response_model=List[NewsArticle],
    summary="Get financial news headlines",
    description="Retrieves latest news headlines and summaries for a symbol.",
    dependencies=[Depends(get_current_user)],
)
async def news(symbol: str) -> List[NewsArticle]:
    return await get_news(symbol)


@router.get(
    "/stream",
    summary="Real-time price tick stream via SSE",
    description="Opens a Server-Sent Events (SSE) connection streaming periodic live price updates for requested symbols.",
    dependencies=[Depends(get_current_user)],
)
async def stream(
    symbols: str = Query("NVDA,AAPL,MSFT,TSLA", description="Comma-separated stock symbols"),
):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        symbol_list = ["NVDA"]

    return StreamingResponse(
        quote_event_generator(symbol_list),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
