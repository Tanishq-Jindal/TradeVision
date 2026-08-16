import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_buy_stock_success(async_client: AsyncClient):
    """Verify buying stock deducts cash, creates position, trade, and transaction."""
    # 1. Register user
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "trader1@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Buy 10 shares of NVDA at fixed test price $120.00 ($1,200 total)
    buy_res = await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "NVDA", "quantity": 10.0, "price": 120.00},
    )
    assert buy_res.status_code == 201
    trade = buy_res.json()
    assert trade["symbol"] == "NVDA"
    assert trade["side"] == "BUY"
    assert trade["quantity"] == 10.0
    assert trade["price"] == 120.00
    assert trade["total_value"] == 1200.00

    # 3. Check portfolio summary
    summary_res = await async_client.get("/api/v1/portfolio/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["cash_balance"] == 98800.00
    assert summary["positions_count"] == 1

    # 4. Check positions
    pos_res = await async_client.get("/api/v1/portfolio/positions", headers=headers)
    assert pos_res.status_code == 200
    positions = pos_res.json()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "NVDA"
    assert positions[0]["quantity"] == 10.0
    assert positions[0]["avg_entry_price"] == 120.00


@pytest.mark.asyncio
async def test_buy_stock_insufficient_cash(async_client: AsyncClient):
    """Verify order is rejected when total value exceeds available cash balance."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "poor_trader@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # User has $100,000. Attempt to buy $200,000 worth (1000 shares @ $200)
    buy_res = await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "AAPL", "quantity": 1000.0, "price": 200.00},
    )
    assert buy_res.status_code == 422
    data = buy_res.json()
    assert data["error"]["code"] == "INSUFFICIENT_CASH"


@pytest.mark.asyncio
async def test_consecutive_buys_weighted_average(async_client: AsyncClient):
    """Verify multiple buy orders compute the correct weighted average entry price."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "avg_trader@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Buy 10 @ $100 ($1,000)
    await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "MSFT", "quantity": 10.0, "price": 100.00},
    )

    # Buy 10 @ $200 ($2,000) -> Total 20 shares, $3,000 invested -> Avg $150.00
    await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "MSFT", "quantity": 10.0, "price": 200.00},
    )

    pos_res = await async_client.get("/api/v1/portfolio/positions", headers=headers)
    positions = pos_res.json()
    assert len(positions) == 1
    assert positions[0]["quantity"] == 20.0
    assert positions[0]["avg_entry_price"] == 150.00


@pytest.mark.asyncio
async def test_sell_stock_success_and_insufficient_shares(async_client: AsyncClient):
    """Verify selling reduces shares, credits cash, and prevents overselling."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "seller@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Buy 20 shares of TSLA @ $200 ($4,000 total) -> Cash is $96,000
    await async_client.post(
        "/api/v1/trades/buy",
        headers=headers,
        json={"symbol": "TSLA", "quantity": 20.0, "price": 200.00},
    )

    # Attempt to sell 30 shares (more than 20 held) -> Should fail
    oversell_res = await async_client.post(
        "/api/v1/trades/sell",
        headers=headers,
        json={"symbol": "TSLA", "quantity": 30.0, "price": 250.00},
    )
    assert oversell_res.status_code == 422
    assert oversell_res.json()["error"]["code"] == "INSUFFICIENT_SHARES"

    # Sell 10 shares @ $250 ($2,500 total) -> Cash becomes $96,000 + $2,500 = $98,500
    sell_res = await async_client.post(
        "/api/v1/trades/sell",
        headers=headers,
        json={"symbol": "TSLA", "quantity": 10.0, "price": 250.00},
    )
    assert sell_res.status_code == 201

    summary_res = await async_client.get("/api/v1/portfolio/summary", headers=headers)
    assert summary_res.json()["cash_balance"] == 98500.00

    # Sell remaining 10 shares -> Position deleted
    sell_all = await async_client.post(
        "/api/v1/trades/sell",
        headers=headers,
        json={"symbol": "TSLA", "quantity": 10.0, "price": 250.00},
    )
    assert sell_all.status_code == 201

    pos_res = await async_client.get("/api/v1/portfolio/positions", headers=headers)
    assert len(pos_res.json()) == 0


@pytest.mark.asyncio
async def test_trading_orders_buy_and_sell_unified_endpoint(async_client: AsyncClient):
    """Verify POST /api/v1/trading/orders executes market BUY and SELL orders atomically."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "order_user@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Submit Market BUY order
    buy_order = {
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 15,
        "order_type": "MARKET",
        "price": 200.00,
    }
    buy_res = await async_client.post(
        "/api/v1/trading/orders",
        headers=headers,
        json=buy_order,
    )
    assert buy_res.status_code == 201
    trade = buy_res.json()
    assert trade["symbol"] == "AAPL"
    assert trade["side"] == "BUY"
    assert trade["quantity"] == 15
    assert trade["total_value"] == 3000.00

    # 2. Check full Portfolio endpoint GET /api/v1/portfolio
    portfolio_res = await async_client.get("/api/v1/portfolio", headers=headers)
    assert portfolio_res.status_code == 200
    p_data = portfolio_res.json()
    assert p_data["cash_balance"] == 97000.00
    assert len(p_data["positions"]) == 1
    assert p_data["positions"][0]["symbol"] == "AAPL"
    assert p_data["positions"][0]["quantity"] == 15
    assert p_data["positions"][0]["average_cost"] == 200.00

    # 3. Check orders history GET /api/v1/trading/orders/history
    history_res = await async_client.get("/api/v1/trading/orders/history", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1
    assert history_res.json()[0]["symbol"] == "AAPL"

    # 4. Submit Market SELL order
    sell_order = {
        "symbol": "AAPL",
        "side": "SELL",
        "quantity": 5,
        "order_type": "MARKET",
        "price": 220.00,
    }
    sell_res = await async_client.post(
        "/api/v1/trading/orders",
        headers=headers,
        json=sell_order,
    )
    assert sell_res.status_code == 201
    assert sell_res.json()["quantity"] == 5

    # 5. Verify remaining position quantity is 10
    portfolio_res2 = await async_client.get("/api/v1/portfolio", headers=headers)
    assert portfolio_res2.status_code == 200
    p_data2 = portfolio_res2.json()
    assert p_data2["cash_balance"] == 98100.00
    assert p_data2["positions"][0]["quantity"] == 10


@pytest.mark.asyncio
async def test_multi_watchlists_crud_and_cross_user_isolation(async_client: AsyncClient):
    """Verify multi-watchlist creation, items management, and cross-user authorization barriers."""
    # User 1
    reg1 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "wl_owner@example.com", "password": "password123"},
    )
    token1 = reg1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # User 2
    reg2 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "wl_attacker@example.com", "password": "password123"},
    )
    token2 = reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates a watchlist
    create_res = await async_client.post("/api/v1/watchlists", headers=headers1)
    assert create_res.status_code == 201
    wl_id = create_res.json()["id"]

    # User 1 adds AMZN to watchlist
    add_res = await async_client.post(
        f"/api/v1/watchlists/{wl_id}/items",
        headers=headers1,
        json={"symbol": "AMZN"},
    )
    assert add_res.status_code == 201
    assert add_res.json()["symbol"] == "AMZN"

    # User 1 duplicate add -> 409 Conflict
    dup_res = await async_client.post(
        f"/api/v1/watchlists/{wl_id}/items",
        headers=headers1,
        json={"symbol": "AMZN"},
    )
    assert dup_res.status_code == 409

    # User 2 attempts to access User 1's watchlist items -> 403 Forbidden
    cross_access = await async_client.get(
        f"/api/v1/watchlists/{wl_id}/items",
        headers=headers2,
    )
    assert cross_access.status_code == 403

    # User 2 attempts to delete User 1's watchlist -> 403 Forbidden
    cross_del = await async_client.delete(
        f"/api/v1/watchlists/{wl_id}",
        headers=headers2,
    )
    assert cross_del.status_code == 403

    # User 1 deletes AMZN item
    del_item = await async_client.delete(
        f"/api/v1/watchlists/{wl_id}/items/AMZN",
        headers=headers1,
    )
    assert del_item.status_code == 200

    # User 1 deletes watchlist
    del_wl = await async_client.delete(
        f"/api/v1/watchlists/{wl_id}",
        headers=headers1,
    )
    assert del_wl.status_code == 200
