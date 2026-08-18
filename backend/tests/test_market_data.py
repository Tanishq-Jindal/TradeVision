import pytest
from httpx import AsyncClient
from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_momentum,
    calculate_volume_ratio,
)


@pytest.mark.asyncio
async def test_symbol_search_autocomplete(async_client: AsyncClient):
    """Verify searching for symbol or company name returns matching tickers."""
    # Search ticker
    res_nvda = await async_client.get("/api/v1/market/search?q=NVDA")
    assert res_nvda.status_code == 200
    data_nvda = res_nvda.json()
    assert len(data_nvda) > 0
    assert any(item["symbol"] == "NVDA" for item in data_nvda)

    # Search company name
    res_apple = await async_client.get("/api/v1/market/search?q=Apple")
    assert res_apple.status_code == 200
    data_apple = res_apple.json()
    assert any(item["symbol"] == "AAPL" for item in data_apple)


@pytest.mark.asyncio
async def test_get_quote_structure_and_real_data_flag(async_client: AsyncClient):
    """Verify quote endpoint returns real price fields, positive prices, and real provider status."""
    # Register and authenticate
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "market_user@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/market/quote/NVDA", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "NVDA"
    assert data["current_price"] > 0
    assert "change" in data
    assert "change_percent" in data
    assert data["high"] >= data["low"]
    assert data["open"] > 0
    assert data["previous_close"] > 0
    assert data["simulated"] is False
    assert "provider" in data
    assert "market_status" in data


@pytest.mark.asyncio
async def test_unknown_symbol_returns_404(async_client: AsyncClient):
    """Verify requesting quote for an unknown symbol returns 404 with error envelope."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "unknown_sym_user@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/market/quote/NONEXISTENT999XYZ", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_ohlcv_candlestick_data(async_client: AsyncClient):
    """Verify OHLCV endpoint returns chronological candle bars with high/low bounds."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "ohlcv_user@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/market/ohlcv/AAPL?count=30", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "AAPL"
    candles = data["candles"]
    assert len(candles) > 0

    for c in candles:
        assert c["high"] >= c["low"]
        assert c["high"] >= c["open"]
        assert c["high"] >= c["close"]
        assert c["low"] <= c["open"]
        assert c["low"] <= c["close"]
        assert c["volume"] >= 0


@pytest.mark.asyncio
async def test_get_news_endpoint(async_client: AsyncClient):
    """Verify news endpoint returns headlines and sources."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "news_user@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/market/news/TSLA", headers=headers)
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) > 0
    for art in articles:
        assert art["symbol"] == "TSLA"
        assert "headline" in art
        assert "summary" in art
        assert "source" in art


@pytest.mark.asyncio
async def test_get_market_movers_endpoint(async_client: AsyncClient):
    """Verify market movers endpoint returns top gainers and losers sorted dynamically."""
    response = await async_client.get("/api/v1/market/movers?limit=6")
    assert response.status_code == 200
    data = response.json()

    assert "gainers" in data
    assert "losers" in data
    assert len(data["gainers"]) > 0
    assert len(data["losers"]) > 0
    assert data["simulated"] is False

    # Verify gainers are sorted descending by percentage change
    g_pcts = [g["change_percent"] for g in data["gainers"]]
    assert g_pcts == sorted(g_pcts, reverse=True)

    # Verify losers are sorted ascending by percentage change
    l_pcts = [l["change_percent"] for l in data["losers"]]
    assert l_pcts == sorted(l_pcts)

    # Check mover fields
    top_gainer = data["gainers"][0]
    assert "rank" in top_gainer
    assert "symbol" in top_gainer
    assert "company" in top_gainer
    assert "price" in top_gainer
    assert "change" in top_gainer
    assert "change_percent" in top_gainer


@pytest.mark.asyncio
async def test_get_market_pulse_endpoint(async_client: AsyncClient):
    """Verify global market pulse endpoint returns real major indices."""
    response = await async_client.get("/api/v1/market/pulse")
    assert response.status_code == 200
    data = response.json()

    assert "indices" in data
    assert len(data["indices"]) == 4
    assert data["simulated"] is False

    names = [idx["name"] for idx in data["indices"]]
    assert "S&P 500" in names
    assert "NASDAQ" in names
    assert "DOW JONES" in names
    assert "VIX" in names

    for idx in data["indices"]:
        assert idx["price"] > 0
        assert "change" in idx
        assert "change_percent" in idx
        assert "market_status" in idx


def test_technical_indicators():
    """Verify mathematical correctness of pure-function indicator formulas."""
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0]

    # SMA 5-period on [10..14] = 60/5 = 12.0
    sma5 = calculate_sma(prices, 5)
    assert sma5[0] is None
    assert sma5[4] == 12.0

    # EMA 5-period
    ema5 = calculate_ema(prices, 5)
    assert ema5[4] == 12.0
    assert ema5[5] is not None and ema5[5] > 12.0

    # RSI (strictly between 0 and 100)
    rsi14 = calculate_rsi(prices, 14)
    assert rsi14[14] is not None
    assert 0 <= rsi14[14] <= 100

    # MACD
    macd = calculate_macd(prices, fast_period=5, slow_period=10, signal_period=3)
    assert "macd" in macd
    assert "signal" in macd
    assert "hist" in macd

    # Bollinger Bands
    bb = calculate_bollinger_bands(prices, period=10)
    assert bb["upper"][9] is not None
    assert bb["lower"][9] is not None
    assert bb["upper"][9] >= bb["middle"][9] >= bb["lower"][9]

    # Momentum
    mom = calculate_momentum(prices, period=5)
    assert mom[5] is not None

    # Volume Ratio
    volumes = [1000.0] * 25
    vr = calculate_volume_ratio(volumes, 20)
    assert vr[19] is not None
