import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import InsufficientFundsError, NotFoundError, TradeWiseException
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade
from app.models.transaction import Transaction
from app.schemas.trading import (
    OrderRequest,
    PortfolioResponse,
    PortfolioSummaryResponse,
    PositionDetail,
    PositionResponse,
    TradeOrderRequest,
    TradeResponse,
)
from app.services.market_data import get_quote

logger = logging.getLogger(__name__)


async def get_or_create_portfolio(db: AsyncSession, user_id: int, for_update: bool = False) -> Portfolio:
    """
    Retrieves the user's portfolio, optionally with row locking.
    """
    stmt = select(Portfolio).where(Portfolio.user_id == user_id)
    if for_update and db.bind and "sqlite" not in str(db.bind.url):
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        portfolio = Portfolio(user_id=user_id, cash_balance=100000.00)
        db.add(portfolio)
        await db.flush()

    return portfolio


async def execute_buy(db: AsyncSession, user_id: int, order: TradeOrderRequest) -> Trade:
    """
    Executes a paper stock BUY order inside a row-locked transaction.
    """
    portfolio = await get_or_create_portfolio(db, user_id, for_update=True)

    # 1. Resolve execution price from market service
    if order.price and order.price > 0:
        execution_price = order.price
    else:
        quote = await get_quote(order.symbol)
        execution_price = quote.c

    total_value = round(order.quantity * execution_price, 2)
    cash_available = float(portfolio.cash_balance)

    # 2. Balance validation
    if cash_available < total_value:
        raise InsufficientFundsError(
            message=f"Insufficient cash balance for this trade. Required: ${total_value:,.2f}, Available: ${cash_available:,.2f}",
            details={"required": total_value, "available": cash_available, "symbol": order.symbol},
        )

    # 3. Deduct cash balance
    portfolio.cash_balance = round(cash_available - total_value, 2)

    # 4. Update or create Position
    stmt = select(Position).where(
        Position.portfolio_id == portfolio.id,
        Position.symbol == order.symbol,
    )
    if db.bind and "sqlite" not in str(db.bind.url):
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    position = result.scalar_one_or_none()

    if position:
        old_qty = float(position.quantity)
        old_avg = float(position.avg_entry_price)
        new_qty = old_qty + order.quantity
        new_avg = round((old_qty * old_avg + order.quantity * execution_price) / new_qty, 2)
        position.quantity = new_qty
        position.avg_entry_price = new_avg
        position.updated_at = datetime.now(timezone.utc)
    else:
        position = Position(
            portfolio_id=portfolio.id,
            symbol=order.symbol,
            quantity=order.quantity,
            avg_entry_price=round(execution_price, 2),
        )
        db.add(position)

    # 5. Record Trade
    trade = Trade(
        portfolio_id=portfolio.id,
        symbol=order.symbol,
        side="BUY",
        quantity=order.quantity,
        price=round(execution_price, 2),
        total_value=total_value,
    )
    db.add(trade)
    await db.flush()

    # 6. Record Transaction Ledger Entry
    txn = Transaction(
        portfolio_id=portfolio.id,
        type="TRADE",
        amount=-total_value,
        balance_after=float(portfolio.cash_balance),
        related_trade_id=trade.id,
    )
    db.add(txn)

    await db.commit()
    logger.info(f"BUY trade executed: user={user_id} {order.quantity} {order.symbol} @ ${execution_price:,.2f}")
    return trade


async def execute_sell(db: AsyncSession, user_id: int, order: TradeOrderRequest) -> Trade:
    """
    Executes a paper stock SELL order inside a row-locked transaction.
    """
    portfolio = await get_or_create_portfolio(db, user_id, for_update=True)

    # 1. Fetch and lock position
    stmt = select(Position).where(
        Position.portfolio_id == portfolio.id,
        Position.symbol == order.symbol,
    )
    if db.bind and "sqlite" not in str(db.bind.url):
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    position = result.scalar_one_or_none()

    held_qty = float(position.quantity) if position else 0.0
    if not position or held_qty < order.quantity:
        raise TradeWiseException(
            message=f"Insufficient shares to complete sell order. Held: {held_qty}, Requested: {order.quantity}",
            code="INSUFFICIENT_SHARES",
            status_code=422,
            details={"held": held_qty, "requested": order.quantity, "symbol": order.symbol},
        )

    # 2. Resolve execution price
    if order.price and order.price > 0:
        execution_price = order.price
    else:
        quote = await get_quote(order.symbol)
        execution_price = quote.c

    total_value = round(order.quantity * execution_price, 2)

    # 3. Update or delete position
    new_qty = held_qty - order.quantity
    if new_qty <= 0.00001:
        await db.delete(position)
    else:
        position.quantity = new_qty
        position.updated_at = datetime.now(timezone.utc)

    # 4. Increment cash balance
    portfolio.cash_balance = round(float(portfolio.cash_balance) + total_value, 2)

    # 5. Record Trade
    trade = Trade(
        portfolio_id=portfolio.id,
        symbol=order.symbol,
        side="SELL",
        quantity=order.quantity,
        price=round(execution_price, 2),
        total_value=total_value,
    )
    db.add(trade)
    await db.flush()

    # 6. Record Transaction Ledger Entry
    txn = Transaction(
        portfolio_id=portfolio.id,
        type="TRADE",
        amount=total_value,
        balance_after=float(portfolio.cash_balance),
        related_trade_id=trade.id,
    )
    db.add(txn)

    await db.commit()
    logger.info(f"SELL trade executed: user={user_id} {order.quantity} {order.symbol} @ ${execution_price:,.2f}")
    return trade


async def execute_order(db: AsyncSession, user_id: int, order: OrderRequest) -> Trade:
    """
    Unified paper trading order execution for MARKET orders (BUY and SELL).
    """
    if order.side.upper() == "BUY":
        return await execute_buy(
            db,
            user_id,
            TradeOrderRequest(
                symbol=order.symbol,
                quantity=float(order.quantity),
                price=order.price,
                side="BUY",
                order_type=order.order_type,
            ),
        )
    elif order.side.upper() == "SELL":
        return await execute_sell(
            db,
            user_id,
            TradeOrderRequest(
                symbol=order.symbol,
                quantity=float(order.quantity),
                price=order.price,
                side="SELL",
                order_type=order.order_type,
            ),
        )
    else:
        raise TradeWiseException(
            message=f"Unsupported order side: {order.side}. Supported: BUY, SELL",
            code="INVALID_ORDER_SIDE",
            status_code=422,
        )


async def get_user_portfolio_full(db: AsyncSession, user_id: int) -> PortfolioResponse:
    """
    Computes complete portfolio valuation and detailed position breakdowns.
    """
    portfolio = await get_or_create_portfolio(db, user_id)
    stmt = select(Position).where(Position.portfolio_id == portfolio.id).order_by(Position.symbol)
    result = await db.execute(stmt)
    positions_db = result.scalars().all()

    positions_detail: List[PositionDetail] = []
    total_market_value = 0.0
    invested_value = 0.0

    for pos in positions_db:
        quote = await get_quote(pos.symbol)
        qty = float(pos.quantity)
        avg_cost = float(pos.avg_entry_price)
        current_price = quote.c
        market_val = round(qty * current_price, 2)
        cost_basis = round(qty * avg_cost, 2)
        pos_unrealized_pnl = round(market_val - cost_basis, 2)
        pos_unrealized_pnl_pct = round((pos_unrealized_pnl / cost_basis) * 100, 2) if cost_basis > 0 else 0.0

        total_market_value += market_val
        invested_value += cost_basis

        positions_detail.append(
            PositionDetail(
                id=pos.id,
                symbol=pos.symbol,
                quantity=qty,
                average_cost=avg_cost,
                current_price=current_price,
                market_value=market_val,
                unrealized_pnl=pos_unrealized_pnl,
                unrealized_pnl_percent=pos_unrealized_pnl_pct,
                avg_entry_price=avg_cost,
                unrealized_pnl_pct=pos_unrealized_pnl_pct,
                daily_change_pct=quote.dp,
                updated_at=pos.updated_at,
            )
        )

    cash_balance = float(portfolio.cash_balance)
    total_portfolio_value = round(cash_balance + total_market_value, 2)
    unrealized_pnl = round(total_market_value - invested_value, 2)
    unrealized_pnl_percent = round((unrealized_pnl / invested_value) * 100, 2) if invested_value > 0 else 0.0

    return PortfolioResponse(
        cash_balance=cash_balance,
        total_market_value=round(total_market_value, 2),
        total_portfolio_value=total_portfolio_value,
        invested_value=round(invested_value, 2),
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_percent=unrealized_pnl_percent,
        positions=positions_detail,
    )


async def get_portfolio_summary(db: AsyncSession, user_id: int) -> PortfolioSummaryResponse:
    """
    Computes real-time portfolio summary, invested equity, and total/daily P&L.
    """
    portfolio = await get_or_create_portfolio(db, user_id)

    stmt = select(Position).where(Position.portfolio_id == portfolio.id)
    result = await db.execute(stmt)
    positions = result.scalars().all()

    invested_value = 0.0
    daily_pnl = 0.0

    for pos in positions:
        quote = await get_quote(pos.symbol)
        qty = float(pos.quantity)
        market_val = qty * quote.c
        invested_value += market_val
        daily_pnl += qty * quote.d

    cash_balance = float(portfolio.cash_balance)
    total_value = round(cash_balance + invested_value, 2)
    total_pnl = round(total_value - 100000.00, 2)
    total_pnl_pct = round((total_pnl / 100000.00) * 100, 2)

    prev_day_value = total_value - daily_pnl
    if prev_day_value > 0:
        daily_pnl_pct = round((daily_pnl / prev_day_value) * 100, 2)
    else:
        daily_pnl_pct = 0.0

    return PortfolioSummaryResponse(
        cash_balance=cash_balance,
        invested_value=round(invested_value, 2),
        total_value=total_value,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        daily_pnl=round(daily_pnl, 2),
        daily_pnl_pct=daily_pnl_pct,
        positions_count=len(positions),
    )


async def get_user_positions(db: AsyncSession, user_id: int) -> List[PositionResponse]:
    """
    Retrieves held positions with live price, market value, and unrealized P&L.
    """
    portfolio = await get_or_create_portfolio(db, user_id)
    stmt = select(Position).where(Position.portfolio_id == portfolio.id).order_by(Position.symbol)
    result = await db.execute(stmt)
    positions = result.scalars().all()

    responses: List[PositionResponse] = []
    for pos in positions:
        quote = await get_quote(pos.symbol)
        qty = float(pos.quantity)
        avg_entry = float(pos.avg_entry_price)
        current_price = quote.c
        market_val = round(qty * current_price, 2)
        unrealized_pnl = round((current_price - avg_entry) * qty, 2)
        unrealized_pnl_pct = round(((current_price - avg_entry) / avg_entry) * 100, 2) if avg_entry > 0 else 0.0

        responses.append(
            PositionResponse(
                id=pos.id,
                symbol=pos.symbol,
                quantity=qty,
                avg_entry_price=avg_entry,
                current_price=current_price,
                market_value=market_val,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
                daily_change_pct=quote.dp,
                updated_at=pos.updated_at,
            )
        )

    return responses


async def get_user_trades(db: AsyncSession, user_id: int, limit: int = 50) -> List[Trade]:
    """
    Returns recent trade executions for the user.
    """
    portfolio = await get_or_create_portfolio(db, user_id)
    stmt = (
        select(Trade)
        .where(Trade.portfolio_id == portfolio.id)
        .order_by(desc(Trade.executed_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_transactions(db: AsyncSession, user_id: int, limit: int = 50) -> List[Transaction]:
    """
    Returns the cash ledger transaction history for the user.
    """
    portfolio = await get_or_create_portfolio(db, user_id)
    stmt = (
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio.id)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
