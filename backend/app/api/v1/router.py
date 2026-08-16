from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    market,
    trades,
    portfolio,
    watchlist,
    ai,
    backtest,
    swarm,
    command,
    correlation,
    autopilot,
)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_v1_router.include_router(trades.router, prefix="/trades", tags=["Paper Trading"])
api_v1_router.include_router(trades.router, prefix="/trading", tags=["Paper Trading Engine"])
api_v1_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_v1_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])
api_v1_router.include_router(watchlist.router, prefix="/watchlists", tags=["Watchlists"])
api_v1_router.include_router(ai.router, prefix="/ai", tags=["AI Intelligence"])
api_v1_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting Engine"])
api_v1_router.include_router(swarm.router, prefix="/swarm", tags=["Multi-Agent Swarm"])
api_v1_router.include_router(command.router, prefix="/command", tags=["Command Palette"])
api_v1_router.include_router(correlation.router, prefix="/correlation", tags=["Correlation Network"])
api_v1_router.include_router(autopilot.router, prefix="/autopilot", tags=["Guardrailed Autopilot"])
