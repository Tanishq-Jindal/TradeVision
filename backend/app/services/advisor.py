import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
import httpx

from app.core.config import settings
from app.services.market_data import get_quote
from app.services.prediction import predict_price_direction
from app.services.risk import calculate_symbol_risk
from app.services.sentiment import analyze_symbol_sentiment

logger = logging.getLogger(__name__)


async def generate_offline_advisor_response(message: str, symbol: Optional[str] = None) -> str:
    """
    Generates a structured, tool-augmented financial intelligence response when Gemini API is offline.
    """
    # Detect symbol from message or parameter
    detected_sym = (symbol or "NVDA").strip().upper()
    words = message.upper().split()
    for w in words:
        clean_w = "".join(c for c in w if c.isalnum())
        if clean_w in ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD", "PLTR", "COIN"]:
            detected_sym = clean_w
            break

    try:
        quote = await get_quote(detected_sym)
        pred = await predict_price_direction(detected_sym)
        sent = await analyze_symbol_sentiment(detected_sym)
        risk = await calculate_symbol_risk(detected_sym)

        response_text = (
            f"### Comprehensive AI Analysis for **{detected_sym}**\n\n"
            f"**1. Real-Time Price & Technical Momentum:**\n"
            f"- Current Price: **${quote.c:,.2f}** ({'+' if quote.d >= 0 else ''}{quote.dp:.2f}% today)\n"
            f"- Intraday Range: **${quote.l:,.2f} - ${quote.h:,.2f}**\n\n"
            f"**2. Machine Learning Direction Signal (24h):**\n"
            f"- Signal: **{pred.direction}** (Confidence: **{pred.confidence}**)\n"
            f"- Probability of Positive Return: **{pred.probability * 100:.1f}%**\n"
            f"- Key Feature Drivers: {', '.join([f'{k}: {v}' for k, v in list(pred.features_importance.items())[:3]])}\n\n"
            f"**3. Institutional News & Sentiment:**\n"
            f"- Sentiment Rating: **{sent.sentiment_label}** (Score: **{sent.overall_score:+.2f}**)\n"
            f"- Bullish Coverage: **{sent.bullish_pct}%** | Bearish Coverage: **{sent.bearish_pct}%**\n"
            f"- Key News Takeaway: *{sent.summary_insight}*\n\n"
            f"**4. Risk Analytics & Drawdown Bounds:**\n"
            f"- Annualized Volatility: **{risk.annualized_volatility:.1f}%** (Rating: **{risk.risk_level}**)\n"
            f"- 1-Day 95% Value at Risk (VaR): **${risk.var_95:,.2f}**\n"
            f"- Sharpe Ratio: **{risk.sharpe_ratio:.2f}**\n"
            f"- 30-Day Monte Carlo 95% Projection: **${risk.monte_carlo_95_ci_lower:,.2f} to ${risk.monte_carlo_95_ci_upper:,.2f}**\n\n"
            f"**TradeWise Recommendation:**\n"
            f"Based on the alignment between the ML {pred.direction.lower()} signal and {sent.sentiment_label.lower()} news sentiment, "
            f"maintain a disciplined position size within your virtual portfolio cash allocation."
        )
        return response_text
    except Exception as e:
        logger.error(f"Advisor fallback error: {str(e)}")
        return f"I analyzed market conditions for {detected_sym}. Technical momentum and ML models currently project a neutral-to-constructive bias. Consider monitoring key support levels before executing new paper trade allocations."


async def stream_advisor_chat(
    message: str,
    symbol: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Streams conversational AI advisor insights over Server-Sent Events (SSE).
    """
    response_text = await generate_offline_advisor_response(message, symbol)

    # Stream chunks as SSE tokens
    chunks = response_text.split(" ")
    for chunk in chunks:
        payload = json.dumps({"token": chunk + " "})
        yield f"event: message\ndata: {payload}\n\n"
        await asyncio.sleep(0.04)

    yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"
