import asyncio
import logging
import time
from typing import List, Optional
from app.schemas.ai import SignalScanItem
from app.services.indicators import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from app.services.market_data import UNIVERSE, get_ohlcv, get_quote
from app.services.prediction import predict_price_direction
from app.services.sentiment import analyze_symbol_sentiment

logger = logging.getLogger(__name__)

_scanner_cache: List[SignalScanItem] = []
_scanner_cached_at: float = 0.0
SCANNER_TTL = 300  # 5 minutes


async def _scan_single_symbol(sym: str) -> Optional[SignalScanItem]:
    try:
        now = int(time.time())
        quote = await get_quote(sym)
        ohlcv = await get_ohlcv(sym, "1D", 60)
        pred = await predict_price_direction(sym)
        sent = await analyze_symbol_sentiment(sym)

        closes = [c.close for c in ohlcv.candles]
        rsi = calculate_rsi(closes, 14)
        macd_res = calculate_macd(closes, 12, 26, 9)
        bb_res = calculate_bollinger_bands(closes, 20)
        sma_20 = calculate_sma(closes, 20)

        latest_rsi = rsi[-1] or 50.0
        latest_macd_hist = macd_res["hist"][-1] or 0.0
        c_price = closes[-1]
        bb_mid = bb_res["middle"][-1] or c_price
        sma_val = sma_20[-1] or c_price

        # 1. Technical Score (0 - 100)
        tech_score = 50.0
        key_drivers: List[str] = []

        if latest_rsi < 35:
            tech_score += 25
            key_drivers.append(f"RSI Oversold ({latest_rsi:.1f})")
        elif latest_rsi > 65:
            tech_score -= 20
            key_drivers.append(f"RSI Overbought ({latest_rsi:.1f})")

        if latest_macd_hist > 0:
            tech_score += 15
            key_drivers.append("MACD Bullish Histogram")
        else:
            tech_score -= 10

        if c_price > sma_val:
            tech_score += 10
            key_drivers.append("Above 20-Day SMA")
        else:
            tech_score -= 10

        tech_score = max(0.0, min(100.0, tech_score))

        # 2. ML Score (0 - 100)
        ml_score = pred.probability * 100.0
        if pred.direction == "BULLISH":
            key_drivers.append(f"ML Direction: Bullish ({pred.probability*100:.0f}%)")
        elif pred.direction == "BEARISH":
            key_drivers.append(f"ML Direction: Bearish ({(1-pred.probability)*100:.0f}%)")

        # 3. Sentiment Score (0 - 100)
        sent_score = max(0.0, min(100.0, (sent.overall_score + 1.0) * 50.0))
        if sent.overall_score > 0.2:
            key_drivers.append(f"News Sentiment Positive (+{sent.overall_score:.2f})")
        elif sent.overall_score < -0.2:
            key_drivers.append(f"News Sentiment Cautious ({sent.overall_score:.2f})")

        # 4. Composite Score
        composite = round(0.40 * tech_score + 0.35 * ml_score + 0.25 * sent_score, 1)

        if composite >= 78:
            signal_type = "STRONG_BUY"
        elif composite >= 62:
            signal_type = "BUY"
        elif composite <= 25:
            signal_type = "STRONG_SELL"
        elif composite <= 40:
            signal_type = "SELL"
        else:
            signal_type = "NEUTRAL"

        meta = UNIVERSE.get(sym, {"name": sym})

        return SignalScanItem(
            id=f"sig-{sym}-{now}",
            symbol=sym,
            name=meta.get("name", sym),
            signal_type=signal_type,
            composite_score=composite,
            technical_score=round(tech_score, 1),
            ml_prediction_score=round(ml_score, 1),
            sentiment_score=round(sent_score, 1),
            price=quote.c,
            change_pct=quote.dp,
            key_drivers=key_drivers[:3],
            generated_at=now,
        )
    except Exception as e:
        logger.warning(f"Error scanning symbol {sym}: {str(e)}")
        return None


async def scan_market_signals(top_n: int = 10) -> List[SignalScanItem]:
    """
    Scans the equity universe for high-probability multi-factor trade opportunities concurrently.
    """
    global _scanner_cache, _scanner_cached_at
    now = time.time()

    if _scanner_cache and (now - _scanner_cached_at < SCANNER_TTL):
        return _scanner_cache[:top_n]

    symbols_to_scan = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "PLTR", "COIN", "CRM", "NFLX"]
    tasks = [_scan_single_symbol(sym) for sym in symbols_to_scan]
    scanned_items = await asyncio.gather(*tasks)

    results = [item for item in scanned_items if item is not None]
    results.sort(key=lambda x: x.composite_score, reverse=True)

    _scanner_cache = results
    _scanner_cached_at = now

    return results[:top_n]
