import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade
from app.models.transaction import Transaction


@pytest.mark.asyncio
async def test_exact_buy_and_sell_accounting_lifecycle(async_client: AsyncClient):
    """
    Validates the exact math and ledger consistency for BUY followed by SELL:
    1. Initial Cash: $100,000
    2. BUY 10 shares @ $200.00 ($2,000 total) -> Cash = $98,000, Position = 10 shares @ $200.00
    3. SELL 10 shares @ $250.00 ($2,500 total) -> Cash = $100,500, Position = 0 shares (deleted)
    4. Realized gain of +$500.00 reflected in total cash and performance.
    """
    # 1. Register new user
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "accounting_trader@example.com", "password": "Password123"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initial cash is exactly $100,000.00
    p0 = await async_client.get("/api/v1/portfolio", headers=headers)
    assert p0.status_code == 200
    assert p0.json()["cash_balance"] == 100000.00
    assert len(p0.json()["positions"]) == 0

    # 2. BUY 10 shares of NVDA @ $200.00
    buy_res = await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "NVDA", "quantity": 10.0, "price": 200.00},
    )
    assert buy_res.status_code == 201
    buy_trade = buy_res.json()
    assert buy_trade["symbol"] == "NVDA"
    assert buy_trade["side"] == "BUY"
    assert buy_trade["quantity"] == 10.0
    assert buy_trade["price"] == 200.00
    assert buy_trade["total_value"] == 2000.00

    # Verify Cash Balance = $98,000.00 and Holdings = 10 shares
    p1 = await async_client.get("/api/v1/portfolio", headers=headers)
    assert p1.status_code == 200
    p1_data = p1.json()
    assert p1_data["cash_balance"] == 98000.00
    assert len(p1_data["positions"]) == 1
    assert p1_data["positions"][0]["symbol"] == "NVDA"
    assert p1_data["positions"][0]["quantity"] == 10.0
    assert p1_data["positions"][0]["average_cost"] == 200.00

    # Verify Transaction Ledger Entry for BUY
    txns_res = await async_client.get("/api/v1/portfolio/transactions", headers=headers)
    assert txns_res.status_code == 200
    txns = txns_res.json()
    assert len(txns) >= 1
    buy_txn = txns[0]
    assert buy_txn["type"] == "TRADE"
    assert buy_txn["amount"] == -2000.00
    assert buy_txn["balance_after"] == 98000.00

    # 3. SELL 10 shares of NVDA @ $250.00
    sell_res = await async_client.post(
        "/api/v1/trades/sell",
        headers=headers,
        json={"symbol": "NVDA", "quantity": 10.0, "price": 250.00},
    )
    assert sell_res.status_code == 201
    sell_trade = sell_res.json()
    assert sell_trade["symbol"] == "NVDA"
    assert sell_trade["side"] == "SELL"
    assert sell_trade["quantity"] == 10.0
    assert sell_trade["price"] == 250.00
    assert sell_trade["total_value"] == 2500.00

    # Verify Cash Balance = $100,500.00 and Position is closed (0 positions)
    p2 = await async_client.get("/api/v1/portfolio", headers=headers)
    assert p2.status_code == 200
    p2_data = p2.json()
    assert p2_data["cash_balance"] == 100500.00
    assert len(p2_data["positions"]) == 0
    assert p2_data["total_portfolio_value"] == 100500.00

    # Verify Summary calculations reflect +$500.00 total return (+0.5%)
    summary_res = await async_client.get("/api/v1/portfolio/summary", headers=headers)
    assert summary_res.status_code == 200
    s_data = summary_res.json()
    assert s_data["cash_balance"] == 100500.00
    assert s_data["total_value"] == 100500.00
    assert s_data["total_pnl"] == 500.00
    assert s_data["total_pnl_pct"] == 0.50

    # Verify Transaction Ledger Entry for SELL
    txns_res2 = await async_client.get("/api/v1/portfolio/transactions", headers=headers)
    assert txns_res2.status_code == 200
    txns2 = txns_res2.json()
    assert len(txns2) >= 2
    sell_txn = txns2[0]  # Latest transaction is first
    assert sell_txn["type"] == "TRADE"
    assert sell_txn["amount"] == 2500.00
    assert sell_txn["balance_after"] == 100500.00


@pytest.mark.asyncio
async def test_buy_insufficient_funds_rejected_and_cash_unchanged(async_client: AsyncClient):
    """Verify BUY order exceeding cash balance is rejected and balance is completely untouched."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "insufficient_tester@example.com", "password": "Password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to buy $150,000 of stock when user only has $100,000
    buy_res = await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "TSLA", "quantity": 750.0, "price": 200.00},
    )
    assert buy_res.status_code == 422
    assert buy_res.json()["error"]["code"] == "INSUFFICIENT_CASH"

    # Cash remains $100,000.00
    p = await async_client.get("/api/v1/portfolio", headers=headers)
    assert p.json()["cash_balance"] == 100000.00
    assert len(p.json()["positions"]) == 0


@pytest.mark.asyncio
async def test_sell_more_shares_than_owned_rejected(async_client: AsyncClient):
    """Verify SELL order exceeding owned share quantity is rejected with 422 INSUFFICIENT_SHARES."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "oversell_tester@example.com", "password": "Password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Buy 5 shares of MSFT
    await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "MSFT", "quantity": 5.0, "price": 100.00},
    )

    # Attempt to sell 10 shares of MSFT
    sell_res = await async_client.post(
        "/api/v1/trades/sell",
        headers=headers,
        json={"symbol": "MSFT", "quantity": 10.0, "price": 100.00},
    )
    assert sell_res.status_code == 422
    assert sell_res.json()["error"]["code"] == "INSUFFICIENT_SHARES"

    # Cash balance remains $99,500.00 ($100k - $500)
    p = await async_client.get("/api/v1/portfolio", headers=headers)
    assert p.json()["cash_balance"] == 99500.00
    assert p.json()["positions"][0]["quantity"] == 5.0
