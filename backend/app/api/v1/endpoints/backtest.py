from fastapi import APIRouter
from app.schemas.backtest import BacktestRequest, BacktestResult
from app.services.backtester import run_backtest

router = APIRouter()


@router.post(
    "/run",
    response_model=BacktestResult,
    summary="Run historical strategy backtest",
    description="Simulates bar-by-bar trading strategy on historical data with Sharpe ratio, maximum drawdown, and equity curve attribution.",
)
async def backtest_strategy(req: BacktestRequest) -> BacktestResult:
    return await run_backtest(req)
