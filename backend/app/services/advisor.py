import asyncio
import hashlib
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


def get_key_fingerprint(api_key: str) -> tuple[str, int, str]:
    """Generates a safe, non-secret SHA-256 fingerprint, length, and preview of an API key."""
    clean_key = (api_key or "").strip().strip("'\"` \r\n\t")
    if clean_key.startswith("GEMINI_API_KEY="):
        clean_key = clean_key[len("GEMINI_API_KEY="):].strip().strip("'\"` \r\n\t")
    if clean_key.startswith("Bearer "):
        clean_key = clean_key[len("Bearer "):].strip().strip("'\"` \r\n\t")
    if not clean_key:
        return "[none]", 0, "[not_set]"
    fp = hashlib.sha256(clean_key.encode("utf-8")).hexdigest()[:12]
    length = len(clean_key)
    preview = f"{clean_key[:4]}...{'*' * max(0, length - 4)}"
    return fp, length, preview


async def get_available_gemini_models(api_key: str) -> tuple[list[str], str]:
    """
    Queries Google Generative Language API for models supporting generateContent for this key.
    Returns: (list_of_model_names, api_status_code_str)
    """
    clean_api_key = (api_key or "").strip().strip("'\"` \r\n\t")
    if clean_api_key.startswith("GEMINI_API_KEY="):
        clean_api_key = clean_api_key[len("GEMINI_API_KEY="):].strip().strip("'\"` \r\n\t")
    if clean_api_key.startswith("Bearer "):
        clean_api_key = clean_api_key[len("Bearer "):].strip().strip("'\"` \r\n\t")

    if not clean_api_key:
        return [], "unconfigured"

    fp, length, _ = get_key_fingerprint(clean_api_key)
    logger.info(f"[Discovery] Querying Gemini models with key_fingerprint={fp}, length={length}")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={"x-goog-api-key": clean_api_key},
            )
            if res.status_code == 200:
                data = res.json()
                raw_models = data.get("models", [])
                supported = []
                for m in raw_models:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        name = m.get("name", "")
                        if name.startswith("models/"):
                            name = name[len("models/"):]
                        if name:
                            supported.append(name)
                logger.info(f"[Discovery] Discovered {len(supported)} Gemini models supporting generateContent: {supported[:5]}")
                return supported, "ok_200"
            elif res.status_code == 401:
                logger.error(f"[Discovery] Google rejected API key with HTTP 401 Unauthorized (fingerprint={fp})")
                return [], "invalid_key_401"
            elif res.status_code == 403:
                logger.error(f"[Discovery] Google returned HTTP 403 Forbidden (fingerprint={fp})")
                return [], "forbidden_403"
            elif res.status_code == 429:
                logger.warning(f"[Discovery] Google returned HTTP 429 Too Many Requests (fingerprint={fp})")
                return [], "rate_limit_429"
            else:
                return [], f"error_{res.status_code}"
    except httpx.TimeoutException:
        logger.warning(f"[Discovery] Timeout connecting to Gemini models endpoint (fingerprint={fp})")
        return [], "timeout"
    except Exception as e:
        logger.warning(f"[Discovery] Could not connect to Gemini models endpoint: {str(e)}")
        return [], "unreachable"


async def get_ai_service_status() -> dict:
    """Returns safe diagnostic information about Gemini AI configuration without exposing secrets."""
    clean_api_key = (settings.GEMINI_API_KEY or "").strip().strip("'\"` \r\n\t")
    if clean_api_key.startswith("GEMINI_API_KEY="):
        clean_api_key = clean_api_key[len("GEMINI_API_KEY="):].strip().strip("'\"` \r\n\t")
    if clean_api_key.startswith("Bearer "):
        clean_api_key = clean_api_key[len("Bearer "):].strip().strip("'\"` \r\n\t")

    fp, length, preview = get_key_fingerprint(clean_api_key)
    logger.info(f"[StatusCheck] key_fingerprint={fp}, length={length}")

    discovered_models, api_status = await get_available_gemini_models(clean_api_key)

    active_model = settings.GEMINI_MODEL or "gemini-2.5-flash"
    if discovered_models and active_model not in discovered_models:
        # Pick best matching model from discovered
        flash_models = [m for m in discovered_models if "flash" in m.lower()]
        active_model = flash_models[0] if flash_models else discovered_models[0]

    return {
        "configured": bool(clean_api_key) and api_status == "ok_200",
        "key_present": bool(clean_api_key),
        "key_length": length,
        "key_preview": preview,
        "model": active_model,
        "google_api_status": api_status,
        "discovered_models": discovered_models,
    }


async def call_gemini_api(prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """
    Direct asynchronous HTTP caller for Google Gemini generateContent REST API.
    Performs dynamic model discovery, candidate selection, safe response diagnostics,
    and robust multi-part content extraction.
    """
    clean_api_key = (api_key or "").strip().strip("'\"` \r\n\t")
    if clean_api_key.startswith("GEMINI_API_KEY="):
        clean_api_key = clean_api_key[len("GEMINI_API_KEY="):].strip().strip("'\"` \r\n\t")
    if clean_api_key.startswith("Bearer "):
        clean_api_key = clean_api_key[len("Bearer "):].strip().strip("'\"` \r\n\t")

    fp, length, _ = get_key_fingerprint(clean_api_key)
    logger.info(f"[CallGemini] Using key_fingerprint={fp}, length={length}")

    if not clean_api_key:
        raise httpx.HTTPStatusError(
            "401 Unauthorized: GEMINI_API_KEY is not configured",
            request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models"),
            response=httpx.Response(401, text="API key not configured"),
        )

    # Discover models dynamically from API
    discovered, api_status = await get_available_gemini_models(clean_api_key)

    if api_status == "invalid_key_401":
        raise httpx.HTTPStatusError(
            "401 Unauthorized: Google rejected the provided Gemini API key",
            request=httpx.Request("GET", "https://generativelanguage.googleapis.com/v1beta/models"),
            response=httpx.Response(401, text="API key not valid"),
        )
    elif api_status == "forbidden_403":
        raise httpx.HTTPStatusError(
            "403 Forbidden: Google Generative Language API is disabled or forbidden",
            request=httpx.Request("GET", "https://generativelanguage.googleapis.com/v1beta/models"),
            response=httpx.Response(403, text="Permission denied"),
        )

    # Prioritize discovered models
    candidate_models = []
    preferred_model = (model_name or settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    if preferred_model.startswith("models/"):
        preferred_model = preferred_model[len("models/"):].strip()

    if discovered:
        if preferred_model in discovered:
            candidate_models.append(preferred_model)
        # Add Flash models
        for m in discovered:
            if "flash" in m.lower() and m not in candidate_models:
                candidate_models.append(m)
        # Add Pro models
        for m in discovered:
            if "pro" in m.lower() and m not in candidate_models:
                candidate_models.append(m)
        # Add any remaining discovered models
        for m in discovered:
            if m not in candidate_models:
                candidate_models.append(m)
    else:
        candidate_models = [preferred_model, "gemini-2.5-flash", "gemini-flash-latest", "gemini-1.5-flash", "gemini-pro"]

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
                url = f"https://generativelanguage.googleapis.com/{api_version}/models/{candidate}:generateContent"
                try:
                    res = await client.post(
                        url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "x-goog-api-key": clean_api_key,
                        },
                    )

                    if res.status_code == 404:
                        logger.warning(f"[GenerateContent] Model {candidate} on {api_version} returned 404. Trying next candidate...")
                        last_error = httpx.HTTPStatusError(
                            f"404 Not Found for model {candidate}",
                            request=res.request,
                            response=res,
                        )
                        continue

                    # Raise for 400, 401, 403, 429, 500
                    res.raise_for_status()

                    data = res.json()

                    # Safe diagnostic logging (NEVER log keys or secrets)
                    logger.info(
                        f"[GenerateContent] HTTP 200 from {candidate} ({api_version}): "
                        f"Content-Type={res.headers.get('content-type')}, "
                        f"JSON_Keys={list(data.keys()) if isinstance(data, dict) else type(data)}, "
                        f"Candidates_Count={len(data.get('candidates', [])) if isinstance(data, dict) else 0}"
                    )

                    # 1. Check for prompt safety blocks
                    feedback = data.get("promptFeedback", {})
                    if feedback.get("blockReason"):
                        block_reason = feedback.get("blockReason")
                        logger.warning(f"[GenerateContent] Prompt blocked by policy: {block_reason}")
                        return f"⚠️ Response blocked by Gemini content policy ({block_reason}). Please try rephrasing your message."

                    # 2. Extract generated text from candidates
                    candidates = data.get("candidates", [])
                    if candidates:
                        for idx, cand in enumerate(candidates):
                            finish_reason = cand.get("finishReason")
                            content = cand.get("content") or {}
                            parts = content.get("parts", [])
                            logger.info(f"Candidate #{idx}: finishReason={finish_reason}, parts_count={len(parts)}")

                            text_chunks = []
                            for p in parts:
                                if isinstance(p, dict) and "text" in p and p["text"]:
                                    text_chunks.append(p["text"])
                                elif isinstance(p, str) and p.strip():
                                    text_chunks.append(p)

                            cand_text = "".join(text_chunks).strip()
                            if cand_text:
                                logger.info(f"[GenerateContent] Successfully received {len(cand_text)} chars from Gemini ({candidate} via {api_version})")
                                return cand_text

                            if finish_reason and finish_reason not in ("STOP", "MAX_TOKENS"):
                                logger.warning(f"Candidate #{idx} terminated with finishReason: {finish_reason}")
                                return f"⚠️ Gemini response filtered by policy ({finish_reason}). Please try a different query."

                    # 3. Check for direct text fields
                    if "text" in data and str(data["text"]).strip():
                        return str(data["text"]).strip()

                    logger.warning(f"[GenerateContent] Model {candidate} on {api_version} returned 200 with no text. Trying next candidate...")
                    continue
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code in (404, 400, 401, 403):
                        # Try next candidate model if available
                        continue
                    # For server errors / rate limits, re-raise
                    raise e
                except Exception as e:
                    last_error = e
                    continue

    if last_error:
        raise last_error
    return "⚠️ Gemini AI returned an empty response. Please try asking a specific question about a stock (e.g., NVDA, AAPL) or your portfolio."


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
    fp, length, _ = get_key_fingerprint(api_key)
    logger.info(f"[ChatAdvisor] Processing request with key_fingerprint={fp}, length={length}")

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
        if status_code in (400, 401):
            return "⚠️ Invalid Gemini API Key (HTTP 401 Unauthorized). Google rejected the credential configured in Render. Please verify the GEMINI_API_KEY environment variable in Render.", False
        elif status_code == 403:
            return "⚠️ Permission denied (HTTP 403 Forbidden). Please verify your Gemini API key has Generative Language API access enabled.", False
        elif status_code == 404:
            return "⚠️ Gemini model unavailable (HTTP 404 Not Found).", False
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
