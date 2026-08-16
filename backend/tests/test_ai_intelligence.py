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
