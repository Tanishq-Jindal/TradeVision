import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.services.market_data import get_quote
from app.services.prediction import predict_price_direction
from app.services.risk import calculate_symbol_risk
from app.services.sentiment import analyze_symbol_sentiment
from app.services.trading_engine import get_user_portfolio_full

logger = logging.getLogger(__name__)


def get_ai_service_status() -> dict:
    """Returns safe diagnostic information about Gemini AI configuration without exposing secrets."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    return {
        "configured": bool(api_key),
        "model": settings.GEMINI_MODEL or "gemini-1.5-flash",
    }


async def call_gemini_api(prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """
    Direct asynchronous HTTP caller for Google Gemini generateContent REST API.
    Supports automatic candidate fallback across official Gemini models if a specific model returns 404.
    """
    raw_model = (model_name or settings.GEMINI_MODEL or "gemini-1.5-flash").strip()
    if raw_model.startswith("models/"):
        raw_model = raw_model[len("models/"):].strip()

    candidate_models = [raw_model]
    for m in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]:
        if m not in candidate_models:
            candidate_models.append(m)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        },
    }

    last_error: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        for candidate in candidate_models:
            for api_version in ["v1beta", "v1"]:
                url = f"https://generativelanguage.googleapis.com/{api_version}/models/{candidate}:generateContent?key={api_key}"
                try:
                    res = await client.post(
                        url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "x-goog-api-key": api_key,
                        },
                    )
                    if res.status_code == 404:
                        logger.warning(f"Gemini model {candidate} on {api_version} returned 404. Trying next candidate...")
                        continue
                    res.raise_for_status()
                    data = res.json()

                    # Extract generated text from candidates
                    candidates = data.get("candidates", [])
                    if candidates:
                        for cand in candidates:
                            content = cand.get("content") or {}
                            parts = content.get("parts", [])
                            text_chunks = [
                                p.get("text", "") for p in parts
                                if isinstance(p, dict) and p.get("text")
                            ]
                            cand_text = "".join(text_chunks).strip()
                            if cand_text:
                                logger.info(f"Successfully received response from Gemini ({candidate} via {api_version})")
                                return cand_text

                    # Check for direct text fields
                    if "text" in data and str(data["text"]).strip():
                        return str(data["text"]).strip()

                    # Check for prompt safety blocks
                    feedback = data.get("promptFeedback", {})
                    if feedback.get("blockReason"):
                        logger.warning(f"Gemini prompt blocked: {feedback.get('blockReason')}")
                        return f"⚠️ Response blocked by safety policy ({feedback.get('blockReason')}). Please try rephrasing your message."

                    logger.warning(f"Gemini model {candidate} on {api_version} returned 200 with no text. Trying next candidate...")
                    continue
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code == 404:
                        continue
                    # For non-404 errors (400, 403, 429), re-raise immediately
                    raise e
                except Exception as e:
                    last_error = e
                    continue

    if last_error:
        raise last_error
    return "Received empty response from Gemini AI. Please try asking a specific stock or portfolio question."


async def get_advisor_chat_response(
    message: str,
    symbol: Optional[str] = None,
    user: Optional[User] = None,
    db: Optional[AsyncSession] = None,
) -> tuple[str, bool]:
    """
    Generates real AI conversational intelligence using Google Gemini API.
    Injects real user portfolio context and live market metrics.
    Returns: (response_text, is_configured)
    """
    # 1. Verify GEMINI_API_KEY is configured
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        error_msg = (
            "⚠️ AI service is not configured. Please set the GEMINI_API_KEY environment variable "
            "in your deployment settings to enable live AI advisory."
        )
        return error_msg, False

    # 2. Extract or resolve target symbol
    detected_sym = (symbol or "NVDA").strip().upper()
    words = message.upper().split()
    for w in words:
        clean_w = "".join(c for c in w if c.isalnum())
        if clean_w in [
            "NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD",
            "PLTR", "COIN", "NFLX", "INTC", "SPY", "QQQ"
        ]:
            detected_sym = clean_w
            break

    # 3. Retrieve real live market analytics
    market_context_lines = []
    try:
        quote = await get_quote(detected_sym)
        pred = await predict_price_direction(detected_sym)
        sent = await analyze_symbol_sentiment(detected_sym)
        risk = await calculate_symbol_risk(detected_sym)

        market_context_lines.extend([
            f"LIVE MARKET DATA FOR {detected_sym}:",
            f"- Current Price: ${quote.c:,.2f} ({'+' if quote.d >= 0 else ''}{quote.d:,.2f}, {'+' if quote.dp >= 0 else ''}{quote.dp:.2f}% today)",
            f"- Intraday High/Low: ${quote.h:,.2f} / ${quote.l:,.2f}",
            f"- ML Direction Prediction: {pred.direction} (Confidence: {pred.confidence}, Positive Return Probability: {pred.probability * 100:.1f}%)",
            f"- News Sentiment: {sent.sentiment_label} (Composite Score: {sent.overall_score:+.2f}, Bullish: {sent.bullish_pct}%, Bearish: {sent.bearish_pct}%)",
            f"- Volatility & Risk: {risk.annualized_volatility:.1f}% Annualized Volatility, 1-Day 95% VaR: ${risk.var_95:,.2f}, Sharpe Ratio: {risk.sharpe_ratio:.2f}",
        ])
    except Exception as e:
        logger.warning(f"Could not retrieve full market context for {detected_sym}: {str(e)}")
        market_context_lines.append(f"MARKET FOCUS: {detected_sym}")

    # 4. Retrieve real user portfolio context if authenticated
    portfolio_context_lines = []
    if user and db:
        try:
            portfolio = await get_user_portfolio_full(db, user.id)
            portfolio_context_lines.extend([
                f"AUTHENTICATED USER PORTFOLIO CONTEXT (SOURCE OF TRUTH):",
                f"- Available Virtual Cash: ${portfolio.cash_balance:,.2f}",
                f"- Total Portfolio Valuation: ${portfolio.total_portfolio_value:,.2f}",
                f"- Total Invested Equity: ${portfolio.invested_value:,.2f}",
                f"- Unrealized P&L: ${portfolio.unrealized_pnl:,.2f} ({portfolio.unrealized_pnl_percent:+.2f}%)",
            ])
            if portfolio.positions:
                pos_summaries = [
                    f"{p.symbol}: {p.quantity} shares @ avg ${p.average_cost:,.2f} (Current: ${p.current_price:,.2f}, P&L: ${p.unrealized_pnl:,.2f})"
                    for p in portfolio.positions
                ]
                portfolio_context_lines.append(f"- Active Holdings: {'; '.join(pos_summaries)}")
            else:
                portfolio_context_lines.append("- Active Holdings: None (100% Cash)")
        except Exception as e:
            logger.warning(f"Could not fetch portfolio context for user {user.id}: {str(e)}")

    # 5. Build prompt
    prompt = (
        "You are TradeVision AI, an expert quantitative trading assistant and portfolio advisor embedded in the TradeVision terminal.\n\n"
        + ("\n".join(portfolio_context_lines) + "\n\n" if portfolio_context_lines else "")
        + ("\n".join(market_context_lines) + "\n\n" if market_context_lines else "")
        + f"USER MESSAGE:\n\"{message}\"\n\n"
        + "INSTRUCTIONS:\n"
        + "1. Respond directly, concisely, and insightfully to the user's question.\n"
        + "2. When discussing the user's balance or holdings, ALWAYS use the exact figures from the Portfolio Context above. NEVER invent fake numbers or accounts.\n"
        + "3. When discussing stock tickers, use the live market data and ML/sentiment metrics provided above.\n"
        + "4. Clearly distinguish educational/paper-trading analysis from verified financial advice.\n"
        + "5. Format your output with clean GitHub markdown headers, bullet points, and bold text."
    )

    # 6. Call Google Gemini API
    try:
        response_text = await call_gemini_api(prompt, api_key)
        return response_text, True
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        logger.error(f"Gemini API HTTP {status_code} error: {e.response.text}")
        if status_code == 400:
            return "⚠️ Invalid Gemini API Key or malformed request. Please check your GEMINI_API_KEY setting.", False
        elif status_code == 403:
            return "⚠️ Permission denied (HTTP 403). Please verify your GEMINI_API_KEY has Generative Language API permissions in Google AI Studio.", False
        elif status_code == 404:
            return "⚠️ Gemini model not found (HTTP 404). Please ensure the Generative Language API is enabled in your Google AI Studio account.", False
        elif status_code == 429:
            return "⚠️ Gemini API rate limit reached. Please wait a moment and try again.", False
        return f"⚠️ Gemini API service returned status {status_code}. Please verify your API key.", False
    except Exception as e:
        logger.error(f"Gemini API request failed: {str(e)}")
        return f"⚠️ Failed to communicate with Gemini AI ({str(e)}). Please verify your network and GEMINI_API_KEY.", False


async def stream_advisor_chat(
    message: str,
    symbol: Optional[str] = None,
    user: Optional[User] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    """
    Streams conversational AI advisor insights over Server-Sent Events (SSE).
    """
    response_text, is_configured = await get_advisor_chat_response(
        message=message,
        symbol=symbol,
        user=user,
        db=db,
    )

    if not is_configured:
        payload = json.dumps({"token": response_text, "error": response_text, "configured": False})
        yield f"event: message\ndata: {payload}\n\n"
        yield f"event: done\ndata: {json.dumps({'status': 'unconfigured'})}\n\n"
        return

    # Stream real Gemini tokens
    chunks = response_text.split(" ")
    for chunk in chunks:
        payload = json.dumps({"token": chunk + " ", "configured": True})
        yield f"event: message\ndata: {payload}\n\n"
        await asyncio.sleep(0.015)

    yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"
