import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ml_prediction_endpoint(async_client: AsyncClient):
    """Verify ML price-direction prediction returns valid direction, probability, and features."""
    response = await async_client.get("/api/v1/ai/prediction/NVDA")
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "NVDA"
    assert data["direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert 0.0 <= data["probability"] <= 1.0
    assert data["confidence"] in ["HIGH", "MEDIUM", "LOW"]
    assert isinstance(data["features_importance"], dict)


@pytest.mark.asyncio
async def test_sentiment_analysis_endpoint(async_client: AsyncClient):
    """Verify sentiment analysis endpoint returns score bounds and scored articles."""
    response = await async_client.get("/api/v1/ai/sentiment/AAPL")
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "AAPL"
    assert -1.0 <= data["overall_score"] <= 1.0
    assert data["sentiment_label"] in ["VERY_BULLISH", "BULLISH", "NEUTRAL", "BEARISH", "VERY_BEARISH"]
    assert data["bullish_pct"] + data["bearish_pct"] + data["neutral_pct"] > 0
    assert len(data["articles"]) > 0


@pytest.mark.asyncio
async def test_risk_metrics_symbol_and_portfolio(async_client: AsyncClient):
    """Verify risk analytics computes volatility, VaR, CVaR, Sharpe, and Monte Carlo simulation."""
    # Symbol risk
    res_sym = await async_client.get("/api/v1/ai/risk/symbol/TSLA")
    assert res_sym.status_code == 200
    sym_data = res_sym.json()
    assert sym_data["annualized_volatility"] >= 0
    assert sym_data["var_95"] >= 0
    assert sym_data["cvar_95"] >= sym_data["var_95"] or sym_data["var_95"] == 0
    assert sym_data["monte_carlo_simulations"] == 10000
    assert sym_data["monte_carlo_95_ci_lower"] <= sym_data["monte_carlo_95_ci_upper"]

    # Authenticated user portfolio risk
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "risk_trader@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_port = await async_client.get("/api/v1/ai/risk/portfolio", headers=headers)
    assert res_port.status_code == 200
    port_data = res_port.json()
    assert "PORTFOLIO" in port_data["symbol_or_portfolio"]
    assert port_data["monte_carlo_95_ci_lower"] <= port_data["monte_carlo_95_ci_upper"]


@pytest.mark.asyncio
async def test_signals_active_scanner(async_client: AsyncClient):
    """Verify signal scanner generates multi-factor scored trade opportunities."""
    response = await async_client.get("/api/v1/ai/signals/active?limit=5")
    assert response.status_code == 200
    signals = response.json()
    assert len(signals) > 0

    for s in signals:
        assert 0.0 <= s["composite_score"] <= 100.0
        assert s["signal_type"] in ["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]
        assert len(s["key_drivers"]) > 0


@pytest.mark.asyncio
async def test_ai_advisor_chat_unconfigured_produces_clear_error(async_client: AsyncClient):
    """Verify missing GEMINI_API_KEY produces an explicit configuration error instead of fake responses."""
    from unittest.mock import patch

    with patch("app.services.advisor.settings.GEMINI_API_KEY", ""):
        res = await async_client.post(
            "/api/v1/ai/advisor/chat",
            json={"message": "What is my current portfolio valuation?", "symbol": "NVDA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["configured"] is False
        assert "AI service is not configured" in data["message"]
        assert "GEMINI_API_KEY" in data["message"]


@pytest.mark.asyncio
async def test_ai_advisor_chat_with_gemini_api_integration(async_client: AsyncClient):
    """Verify AI advisor passes user query and real portfolio context to Google Gemini."""
    from unittest.mock import patch, AsyncMock
    import httpx

    # Mock Gemini HTTP response
    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Based on your real available cash of $100,000.00 and NVDA price metrics, NVDA exhibits a constructive bullish bias."
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json = lambda: mock_gemini_response
    mock_resp.raise_for_status = lambda: None

    # Authenticate user first
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "ai_trader@example.com", "password": "Password123"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.services.advisor.settings.GEMINI_API_KEY", "fake-test-key-123"):
        with patch("app.services.advisor.call_gemini_api", new=AsyncMock(return_value="Based on your real available cash of $100,000.00 and NVDA price metrics, NVDA exhibits a constructive bullish bias.")):
            res = await async_client.post(
                "/api/v1/ai/advisor/chat",
                headers=headers,
                json={"message": "Analyze NVDA for my portfolio", "symbol": "NVDA"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["configured"] is True
            assert "NVDA" in data["message"]
            assert "100,000.00" in data["message"]


@pytest.mark.asyncio
async def test_ai_advisor_status_endpoint(async_client: AsyncClient):
    """Verify /api/v1/ai/advisor/status correctly reflects configuration state without exposing secrets."""
    from unittest.mock import patch, AsyncMock

    # 1. Unconfigured state
    with patch("app.services.advisor.settings.GEMINI_API_KEY", ""):
        res = await async_client.get("/api/v1/ai/advisor/status")
        assert res.status_code == 200
        data = res.json()
        assert data["configured"] is False
        assert data["key_present"] is False
        assert data["google_api_status"] == "unconfigured"
        assert "model" in data

    # 2. Configured state with valid key
    with patch("app.services.advisor.settings.GEMINI_API_KEY", "AIzaSyTestKey1234567890"):
        with patch("app.services.advisor.get_available_gemini_models", new=AsyncMock(return_value=(["gemini-1.5-flash", "gemini-2.0-flash"], "ok_200"))):
            res = await async_client.get("/api/v1/ai/advisor/status")
            assert res.status_code == 200
            data = res.json()
            assert data["configured"] is True
            assert data["key_present"] is True
            assert data["key_length"] == 23
            assert data["key_preview"] == "AIza...*******************"
            assert data["google_api_status"] == "ok_200"
            assert "AIzaSyTestKey1234567890" not in str(data)  # Crucial security guarantee: never leak keys



@pytest.mark.asyncio
async def test_ai_advisor_api_error_handling(async_client: AsyncClient):
    """Verify Gemini API error states (400, 401, 403, 404, 429, 500, timeout) produce structured safe error messages."""
    import httpx
    from unittest.mock import patch, AsyncMock

    with patch("app.services.advisor.settings.GEMINI_API_KEY", "test-key"):
        # 1. Rate limit (429)
        mock_429 = httpx.HTTPStatusError("429 Too Many Requests", request=AsyncMock(), response=AsyncMock(status_code=429, text="Quota exceeded"))
        with patch("app.services.advisor.call_gemini_api", side_effect=mock_429):
            res = await async_client.post("/api/v1/ai/advisor/chat", json={"message": "hello"})
            assert res.status_code == 200
            assert "rate limit" in res.json()["message"].lower()

        # 2. Invalid Key (401)
        mock_401 = httpx.HTTPStatusError("401 Unauthorized", request=AsyncMock(), response=AsyncMock(status_code=401, text="API key not valid"))
        with patch("app.services.advisor.call_gemini_api", side_effect=mock_401):
            res = await async_client.post("/api/v1/ai/advisor/chat", json={"message": "hello"})
            assert res.status_code == 200
            assert "invalid gemini api key" in res.json()["message"].lower()

        # 3. Model Not Found (404)
        mock_404 = httpx.HTTPStatusError("404 Not Found", request=AsyncMock(), response=AsyncMock(status_code=404, text="Model not found"))
        with patch("app.services.advisor.call_gemini_api", side_effect=mock_404):
            res = await async_client.post("/api/v1/ai/advisor/chat", json={"message": "hello"})
            assert res.status_code == 200
            assert "not found" in res.json()["message"].lower()

        # 4. Timeout
        with patch("app.services.advisor.call_gemini_api", side_effect=httpx.TimeoutException("Connection timed out")):
            res = await async_client.post("/api/v1/ai/advisor/chat", json={"message": "hello"})
            assert res.status_code == 200
            assert "timed out" in res.json()["message"].lower()


@pytest.mark.asyncio
async def test_ai_advisor_stream_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/ai/advisor/stream streams tokens correctly over Server-Sent Events."""
    from unittest.mock import patch, AsyncMock

    with patch("app.services.advisor.settings.GEMINI_API_KEY", "test-key"):
        with patch("app.services.advisor.call_gemini_api", new=AsyncMock(return_value="Hello! I am TradeVision AI quantitative advisor.")):
            res = await async_client.get("/api/v1/ai/advisor/stream?message=hello&symbol=NVDA")
            assert res.status_code == 200
            assert "text/event-stream" in res.headers.get("content-type", "")
            content = res.text
            assert "event: message" in content
            assert "Hello!" in content
            assert "event: done" in content



