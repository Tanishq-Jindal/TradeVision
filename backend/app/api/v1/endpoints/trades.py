from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.trading import OrderRequest, TradeOrderRequest, TradeResponse
from app.services.trading_engine import execute_buy, execute_order, execute_sell, get_user_trades

router = APIRouter()


@router.post(
    "/orders",
    response_model=TradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a paper trading order",
    description="Unified MARKET order execution endpoint for BUY or SELL.",
)
async def submit_order(
    order: OrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeResponse:
    trade = await execute_order(db, current_user.id, order)
    return TradeResponse.model_validate(trade)


@router.get(
    "/orders/history",
    response_model=List[TradeResponse],
    summary="Get user order execution history",
    description="Returns chronological order execution history.",
)
async def order_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TradeResponse]:
    trades = await get_user_trades(db, current_user.id, limit=limit)
    return [TradeResponse.model_validate(t) for t in trades]


@router.post(
    "/buy",
    response_model=TradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a paper stock BUY order",
    description="Validates cash balance, executes buy order at live market price, updates or creates position, and writes trade & transaction records inside a locked transaction.",
)
async def buy_stock(
    order: TradeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeResponse:
    trade = await execute_buy(db, current_user.id, order)
    return TradeResponse.model_validate(trade)


@router.post(
    "/sell",
    response_model=TradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a paper stock SELL order",
    description="Validates share quantity, executes sell order at live market price, computes realized P&L, updates or closes position, and updates cash ledger inside a locked transaction.",
)
async def sell_stock(
    order: TradeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TradeResponse:
    trade = await execute_sell(db, current_user.id, order)
    return TradeResponse.model_validate(trade)


@router.get(
    "/history",
    response_model=List[TradeResponse],
    summary="Get user trade execution history",
    description="Returns chronological trade execution history.",
)
async def trade_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TradeResponse]:
    trades = await get_user_trades(db, current_user.id, limit=limit)
    return [TradeResponse.model_validate(t) for t in trades]
