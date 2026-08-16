from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.trading import (
    PortfolioResponse,
    PortfolioSummaryResponse,
    PositionResponse,
    TransactionResponse,
)
from app.services.trading_engine import (
    get_portfolio_summary,
    get_user_portfolio_full,
    get_user_positions,
    get_user_transactions,
)

router = APIRouter()


@router.get(
    "",
    response_model=PortfolioResponse,
    summary="Get full user portfolio valuation and holdings",
    description="Returns cash balance, total market value, total portfolio value, invested value, unrealized P&L, unrealized P&L percent, and full list of held positions.",
)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioResponse:
    return await get_user_portfolio_full(db, current_user.id)


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get user portfolio performance summary",
    description="Returns cash balance, invested equity, total valuation, total P&L, daily P&L, and open positions count.",
)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioSummaryResponse:
    return await get_portfolio_summary(db, current_user.id)


@router.get(
    "/positions",
    response_model=List[PositionResponse],
    summary="Get user active stock holdings",
    description="Returns active holdings with real-time mark-to-market prices, market values, and unrealized P&L.",
)
async def positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PositionResponse]:
    return await get_user_positions(db, current_user.id)


@router.get(
    "/transactions",
    response_model=List[TransactionResponse],
    summary="Get user cash transactions ledger",
    description="Returns general ledger entries for cash deductions and credits.",
)
async def transactions(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TransactionResponse]:
    txns = await get_user_transactions(db, current_user.id, limit=limit)
    return [TransactionResponse.model_validate(t) for t in txns]
