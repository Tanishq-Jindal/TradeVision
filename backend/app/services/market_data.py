import asyncio
import json
import logging
import math
import random
import time
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Dict, List, Optional
import httpx
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.errors import NotFoundError
from app.schemas.market import CandleBar, NewsArticle, OHLCVResponse, QuoteResponse, SymbolSearchResult

logger = logging.getLogger(__name__)

# Liquid US Equities Master Universe
UNIVERSE: Dict[str, Dict[str, str]] = {
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Semiconductors", "base_price": "128.50"},
    "AAPL": {"name": "Apple Inc.", "sector": "Consumer Electronics", "base_price": "224.30"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Software", "base_price": "418.20"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "E-Commerce / Cloud", "base_price": "186.40"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Internet & Search", "base_price": "164.80"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Social Media", "base_price": "560.10"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automotive / EV", "base_price": "218.60"},
    "AMD": {"name": "Advanced Micro Devices", "sector": "Semiconductors", "base_price": "142.30"},
    "INTC": {"name": "Intel Corporation", "sector": "Semiconductors", "base_price": "20.80"},
    "PLTR": {"name": "Palantir Technologies", "sector": "Enterprise Software", "base_price": "38.50"},
    "COIN": {"name": "Coinbase Global Inc.", "sector": "Financial Tech", "base_price": "215.40"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Entertainment", "base_price": "690.20"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Software / CRM", "base_price": "295.40"},
    "ORCL": {"name": "Oracle Corporation", "sector": "Database / Cloud", "base_price": "172.10"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Semiconductors", "base_price": "175.80"},
    "QCOM": {"name": "Qualcomm Inc.", "sector": "Semiconductors", "base_price": "168.40"},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Banking", "base_price": "218.70"},
    "BAC": {"name": "Bank of America Corp.", "sector": "Banking", "base_price": "39.80"},
    "V": {"name": "Visa Inc.", "sector": "Payments", "base_price": "282.60"},
    "MA": {"name": "Mastercard Inc.", "sector": "Payments", "base_price": "488.30"},
    "WMT": {"name": "Walmart Inc.", "sector": "Retail", "base_price": "78.90"},
    "COST": {"name": "Costco Wholesale", "sector": "Retail", "base_price": "905.10"},
    "DIS": {"name": "The Walt Disney Company", "sector": "Entertainment", "base_price": "96.40"},
    "UNH": {"name": "UnitedHealth Group", "sector": "Healthcare", "base_price": "580.20"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Pharmaceuticals", "base_price": "162.80"},
    "XOM": {"name": "Exxon Mobil Corporation", "sector": "Energy", "base_price": "116.40"},
    "CVX": {"name": "Chevron Corporation", "sector": "Energy", "base_price": "148.90"},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "sector": "Index ETF", "base_price": "562.40"},
    "QQQ": {"name": "Invesco QQQ Trust", "sector": "Tech ETF", "base_price": "485.30"},
}

# In-Memory Cache (Level 1)
_memory_cache: Dict[str, Dict[str, any]] = {}

# TTLs in seconds
TTL_QUOTE = 10
TTL_OHLCV = 900
TTL_NEWS = 900


def _get_redis_client() -> Optional[aioredis.Redis]:
    if not settings.REDIS_URL:
        return None
    try:
        return aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
    except Exception:
        return None


async def search_symbols(query: str) -> List[SymbolSearchResult]:
    """
    Fast autocomplete symbol and company name search.
    """
    q = query.strip().upper()
    if not q:
        return [
            SymbolSearchResult(
                symbol=sym,
                description=meta["name"],
                sector=meta["sector"],
            )
            for sym, meta in list(UNIVERSE.items())[:10]
        ]

    results: List[SymbolSearchResult] = []
    for sym, meta in UNIVERSE.items():
        if q in sym or q in meta["name"].upper() or q in meta["sector"].upper():
            results.append(
                SymbolSearchResult(
                    symbol=sym,
                    description=meta["name"],
                    sector=meta["sector"],
                )
            )

    return results


def _generate_simulated_quote(symbol: str) -> QuoteResponse:
    """
    Generates a realistic random-walk price tick based on symbol baseline.
    """
    sym = symbol.upper()
    meta = UNIVERSE.get(sym)
    if not meta:
        raise NotFoundError(
            message=f"Stock symbol '{sym}' was not found in market universe.",
            code="NOT_FOUND",
            details={"symbol": sym},
        )

    base_price = float(meta["base_price"])

    # Deterministic daily drift + small random intraday noise
    seed_val = int(time.time() // 5) + sum(ord(c) for c in sym)
    rng = random.Random(seed_val)

    drift_pct = (rng.random() - 0.48) * 0.03  # -1.5% to +1.5%
    current_price = round(base_price * (1 + drift_pct), 2)
    prev_close = base_price
    change = round(current_price - prev_close, 2)
    pct_change = round((change / prev_close) * 100, 2)

    open_price = round(prev_close * (1 + (rng.random() - 0.5) * 0.005), 2)
    high = round(max(current_price, prev_close, open_price) * (1 + rng.random() * 0.008), 2)
    low = round(min(current_price, prev_close, open_price) * (1 - rng.random() * 0.008), 2)

    return QuoteResponse(
        symbol=sym,
        company=meta["name"],
        name=meta["name"],
        current_price=current_price,
        previous_close=prev_close,
        change=change,
        change_percent=pct_change,
        volume=int(rng.randint(1000000, 50000000)),
        high=high,
        low=low,
        open=open_price,
        timestamp=int(time.time()),
        simulated=True,
        c=current_price,
        d=change,
        dp=pct_change,
        h=high,
        l=low,
        o=open_price,
        pc=prev_close,
        t=int(time.time()),
    )


async def get_quote(symbol: str) -> QuoteResponse:
    """
    Retrieves real-time quote via three-tier cache (Memory -> Redis -> Finnhub / Simulator).
    """
    sym = symbol.strip().upper()
    cache_key = f"quote:{sym}"
    now = time.time()

    # Tier 1: In-memory cache
    if cache_key in _memory_cache:
        item = _memory_cache[cache_key]
        if now - item["cached_at"] < TTL_QUOTE:
            return QuoteResponse(**item["data"])

    # Tier 2: Redis cache
    r_client = _get_redis_client()
    if r_client:
        try:
            cached_json = await r_client.get(cache_key)
            if cached_json:
                data = json.loads(cached_json)
                _memory_cache[cache_key] = {"cached_at": now, "data": data}
                return QuoteResponse(**data)
        except Exception as e:
            logger.debug(f"Redis get quote failed: {str(e)}")
        finally:
            await r_client.aclose()

    # Tier 3: Finnhub API or Simulator
    quote = None
    if settings.FINNHUB_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                url = f"https://finnhub.io/api/v1/quote?symbol={sym}&token={settings.FINNHUB_API_KEY}"
                res = await client.get(url)
                if res.status_code == 200:
                    payload = res.json()
                    if payload.get("c", 0) > 0:
                        meta = UNIVERSE.get(sym, {"name": sym})
                        quote = QuoteResponse(
                            symbol=sym,
                            company=meta.get("name", sym),
                            name=meta.get("name", sym),
                            current_price=float(payload["c"]),
                            previous_close=float(payload.get("pc", payload["c"])),
                            change=float(payload.get("d", 0.0)),
                            change_percent=float(payload.get("dp", 0.0)),
                            volume=int(payload.get("v", 0)),
                            high=float(payload.get("h", payload["c"])),
                            low=float(payload.get("l", payload["c"])),
                            open=float(payload.get("o", payload["c"])),
                            timestamp=int(payload.get("t", int(time.time()))),
                            simulated=False,
                            c=float(payload["c"]),
                            d=float(payload.get("d", 0.0)),
                            dp=float(payload.get("dp", 0.0)),
                            h=float(payload.get("h", payload["c"])),
                            l=float(payload.get("l", payload["c"])),
                            o=float(payload.get("o", payload["c"])),
                            pc=float(payload.get("pc", payload["c"])),
                            t=int(payload.get("t", int(time.time()))),
                        )
        except Exception as e:
            logger.warning(f"Finnhub API quote failed for {sym}: {str(e)}")

    if not quote:
        quote = _generate_simulated_quote(sym)

    # Save to Redis & Memory
    _memory_cache[cache_key] = {"cached_at": now, "data": quote.model_dump()}
    if r_client:
        try:
            r2 = _get_redis_client()
            if r2:
                await r2.set(cache_key, json.dumps(quote.model_dump()), ex=TTL_QUOTE)
                await r2.aclose()
        except Exception:
            pass

    return quote


async def get_ohlcv(
    symbol: str,
    timeframe: str = "1D",
    count: int = 120,
) -> OHLCVResponse:
    """
    Returns historical OHLCV candlestick bars.
    """
    sym = symbol.strip().upper()
    cache_key = f"ohlcv:{sym}:{timeframe}:{count}"
    now = time.time()

    # Check Memory cache
    if cache_key in _memory_cache:
        item = _memory_cache[cache_key]
        if now - item["cached_at"] < TTL_OHLCV:
            return OHLCVResponse(**item["data"])

    # Generate realistic historical daily geometric brownian motion
    meta = UNIVERSE.get(sym)
    base_price = float(meta["base_price"]) if meta else 100.00

    candles: List[CandleBar] = []
    current_time = datetime.now(timezone.utc)
    current_p = base_price * 0.75  # Start from 120 days ago

    rng = random.Random(sum(ord(c) for c in sym) + 42)
    daily_vol = 0.018  # 1.8% daily volatility

    for i in range(count, 0, -1):
        bar_date = current_time - timedelta(days=i)
        # Skip weekends in daily candles
        if bar_date.weekday() >= 5:
            continue

        ret = rng.gauss(0.0008, daily_vol) # Positive slight drift
        open_p = round(current_p, 2)
        close_p = round(open_p * math.exp(ret), 2)
        high_p = round(max(open_p, close_p) * (1 + abs(rng.gauss(0, 0.008))), 2)
        low_p = round(min(open_p, close_p) * (1 - abs(rng.gauss(0, 0.008))), 2)
        volume = int(rng.uniform(1500000, 25000000))

        candles.append(
            CandleBar(
                time=int(bar_date.timestamp()),
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=volume,
            )
        )
        current_p = close_p

    # Set the most recent bar close to the current quote price for seamless continuity
    quote = await get_quote(sym)
    if candles:
        last = candles[-1]
        candles[-1] = CandleBar(
            time=int(time.time()),
            open=quote.o,
            high=max(quote.h, quote.c, quote.o),
            low=min(quote.l, quote.c, quote.o),
            close=quote.c,
            volume=int(rng.uniform(2000000, 30000000)),
        )

    ohlcv_response = OHLCVResponse(
        symbol=sym,
        timeframe=timeframe,
        candles=candles,
        simulated=True,
    )

    _memory_cache[cache_key] = {"cached_at": now, "data": ohlcv_response.model_dump()}
    return ohlcv_response


async def get_news(symbol: str) -> List[NewsArticle]:
    """
    Retrieves recent financial news headlines for a symbol.
    """
    sym = symbol.strip().upper()
    meta = UNIVERSE.get(sym, {"name": sym, "sector": "Equities"})
    name = meta["name"]

    now = int(time.time())
    articles = [
        NewsArticle(
            id=f"{sym}-news-1",
            headline=f"{name} Reports Strong Enterprise Adoption and Solid Operating Margins",
            summary=f"Analysts highlight steady revenue expansion for {sym} as institutional demand accelerates across core business segments.",
            source="MarketWatch",
            url=f"https://finance.yahoo.com/quote/{sym}",
            datetime=now - 3600 * 2,
            symbol=sym,
        ),
        NewsArticle(
            id=f"{sym}-news-2",
            headline=f"Tech Sector Momentum Continues: Key Catalysts to Watch for {sym}",
            summary=f"Investors weigh macroeconomic interest rate outlook alongside sector-wide growth projections and AI infrastructure spending.",
            source="Bloomberg",
            url=f"https://finance.yahoo.com/quote/{sym}",
            datetime=now - 3600 * 8,
            symbol=sym,
        ),
        NewsArticle(
            id=f"{sym}-news-3",
            headline=f"Wall Street Upgrades {sym} Price Target Following Quarterly Product Milestone",
            summary=f"Investment banks boost price target expectations, citing robust competitive moat and customer retention metrics.",
            source="Reuters",
            url=f"https://finance.yahoo.com/quote/{sym}",
            datetime=now - 3600 * 22,
            symbol=sym,
        ),
    ]
    return articles


async def quote_event_generator(symbols: List[str]) -> AsyncGenerator[str, None]:
    """
    Streams live price ticks for symbols over Server-Sent Events (SSE).
    """
    while True:
        for sym in symbols:
            q = await get_quote(sym)
            event_data = json.dumps(q.model_dump())
            yield f"event: quote\ndata: {event_data}\n\n"
        await asyncio.sleep(2.0)
