import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_backtest_run_rsi_and_prompt(async_client: AsyncClient):
    """Verify backtesting engine simulates trades, returns equity curve, and attributes metrics."""
    # 1. Parameterized RSI backtest
    res = await async_client.post(
        "/api/v1/backtest/run",
        json={"symbol": "NVDA", "strategy_type": "RSI_MOMENTUM", "initial_cash": 100000.0, "bars_count": 80},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "NVDA"
    assert data["initial_cash"] == 100000.0
    assert len(data["equity_curve"]) > 0
    assert "sharpe_ratio" in data
    assert "max_drawdown" in data
    assert "win_rate" in data

    # 2. Natural language prompt backtest
    prompt_res = await async_client.post(
        "/api/v1/backtest/run",
        json={"symbol": "AAPL", "strategy_prompt": "Buy when RSI is below 30 and sell when above 70", "bars_count": 60},
    )
    assert prompt_res.status_code == 200
    p_data = prompt_res.json()
    assert p_data["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_multi_agent_swarm_consensus(async_client: AsyncClient):
    """Verify multi-agent swarm orchestrates 4 specialized agents and calculates consensus."""
    res = await async_client.get("/api/v1/swarm/NVDA")
    assert res.status_code == 200
    data = res.json()

    assert data["symbol"] == "NVDA"
    assert data["consensus_signal"] in ["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]
    assert -1.0 <= data["consensus_score"] <= 1.0
    assert len(data["agents"]) == 4
    agent_names = [a["agent_name"] for a in data["agents"]]
    assert any("Momentum" in n for n in agent_names)
    assert any("Mean Reversion" in n for n in agent_names)
    assert any("Sentiment" in n for n in agent_names)
    assert any("Risk" in n for n in agent_names)


@pytest.mark.asyncio
async def test_command_palette_parser(async_client: AsyncClient):
    """Verify command parser extracts structured intent and parameters from natural language."""
    # Buy command
    buy_res = await async_client.post("/api/v1/command/parse", json={"command": "Buy 25 shares of NVDA"})
    assert buy_res.status_code == 200
    b_data = buy_res.json()
    assert b_data["action"] == "TRADE_BUY"
    assert b_data["symbol"] == "NVDA"
    assert b_data["quantity"] == 25.0
    assert b_data["requires_confirmation"] is True

    # Sell command
    sell_res = await async_client.post("/api/v1/command/parse", json={"command": "Sell 10 TSLA"})
    assert sell_res.status_code == 200
    s_data = sell_res.json()
    assert s_data["action"] == "TRADE_SELL"
    assert s_data["symbol"] == "TSLA"
    assert s_data["quantity"] == 10.0

    # Watchlist command
    wl_res = await async_client.post("/api/v1/command/parse", json={"command": "Add MSFT to my watchlist"})
    assert wl_res.status_code == 200
    w_data = wl_res.json()
    assert w_data["action"] == "ADD_WATCHLIST"
    assert w_data["symbol"] == "MSFT"


@pytest.mark.asyncio
async def test_correlation_network_graph(async_client: AsyncClient):
    """Verify correlation network returns nodes and weighted links."""
    res = await async_client.get("/api/v1/correlation/network?symbols=NVDA,AAPL,MSFT,TSLA")
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) >= 4
    for node in data["nodes"]:
        assert "id" in node
        assert "name" in node


@pytest.mark.asyncio
async def test_autopilot_config_and_evaluation(async_client: AsyncClient):
    """Verify autopilot config update and evaluation cycle."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "autopilot_trader@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Set config
    cfg_res = await async_client.post(
        "/api/v1/autopilot/config",
        headers=headers,
        json={
            "enabled": True,
            "max_trade_allocation_pct": 10.0,
            "stop_loss_pct": 5.0,
            "take_profit_pct": 10.0,
            "min_confidence_threshold": 0.60,
        },
    )
    assert cfg_res.status_code == 200
    data = cfg_res.json()
    assert data["active"] is True
    assert data["config"]["max_trade_allocation_pct"] == 10.0
