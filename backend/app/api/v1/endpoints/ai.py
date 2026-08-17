from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AIStatusResponse,
    PredictionResponse,
    RiskMetricResponse,
    SentimentResponse,
    SignalScanItem,
)
from app.services.advisor import get_advisor_chat_response, get_ai_service_status, stream_advisor_chat
from app.services.prediction import predict_price_direction
from app.services.risk import calculate_portfolio_risk, calculate_symbol_risk
from app.services.scanner import scan_market_signals
from app.services.sentiment import analyze_symbol_sentiment

router = APIRouter()


@router.get(
    "/prediction/{symbol}",
    response_model=PredictionResponse,
    summary="Get ML price-direction prediction",
    description="Returns direction (BULLISH/BEARISH/NEUTRAL), probability of positive return, confidence tier, and technical feature importances.",
)
async def get_prediction(symbol: str) -> PredictionResponse:
    return await predict_price_direction(symbol)


@router.get(
    "/sentiment/{symbol}",
    response_model=SentimentResponse,
    summary="Get news sentiment analysis",
    description="Returns financial news sentiment scores, bullish/bearish percentage breakdown, and article sentiment tags.",
)
async def get_sentiment(symbol: str) -> SentimentResponse:
    return await analyze_symbol_sentiment(symbol)


@router.get(
    "/risk/portfolio",
    response_model=RiskMetricResponse,
    summary="Get portfolio-wide risk analytics",
    description="Computes annualized volatility, 95% 1-day Value at Risk (VaR), Conditional VaR (CVaR), Max Drawdown, Sharpe ratio, and 10,000-run Monte Carlo 95% projection bounds.",
)
async def get_portfolio_risk(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskMetricResponse:
    return await calculate_portfolio_risk(db, current_user.id)


@router.get(
    "/risk/symbol/{symbol}",
    response_model=RiskMetricResponse,
    summary="Get stock ticker risk analytics",
    description="Computes standalone volatility, 95% VaR, CVaR, Max Drawdown, and Monte Carlo simulation for a specific stock ticker.",
)
async def get_symbol_risk(symbol: str) -> RiskMetricResponse:
    return await calculate_symbol_risk(symbol)


@router.get(
    "/signals/active",
    response_model=List[SignalScanItem],
    summary="Get active market trade signals",
    description="Runs multi-factor screening across technical indicators, ML price direction predictions, and news sentiment.",
)
async def get_signals(
    limit: int = Query(10, ge=1, le=50),
) -> List[SignalScanItem]:
    return await scan_market_signals(top_n=limit)


@router.post(
    "/advisor/chat",
    response_model=AdvisorChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to conversational AI advisor",
    description="Sends query to real Google Gemini AI model augmented with user portfolio data and live stock metrics.",
)
async def chat_advisor(
    request: AdvisorChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> AdvisorChatResponse:
    response_text, is_configured = await get_advisor_chat_response(
        message=request.message,
        symbol=request.symbol,
        user=current_user,
        db=db,
    )
    return AdvisorChatResponse(
        message=response_text,
        symbol=request.symbol,
        configured=is_configured,
    )


@router.get(
    "/advisor/status",
    response_model=AIStatusResponse,
    summary="Safe AI service diagnostic status",
    description="Returns whether the Gemini API key is configured and active model name without exposing secrets.",
)
async def get_advisor_status() -> AIStatusResponse:
    status_info = await get_ai_service_status()
    return AIStatusResponse(
        configured=status_info["configured"],
        key_present=status_info["key_present"],
        key_length=status_info["key_length"],
        key_preview=status_info["key_preview"],
        model=status_info["model"],
        google_api_status=status_info["google_api_status"],
        discovered_models=status_info.get("discovered_models", []),
    )


@router.get(
    "/advisor/stream",
    summary="Stream conversational AI financial advisor chat (SSE)",
    description="Streams multi-turn conversational financial advice powered by Google Gemini and live portfolio context.",
)
async def stream_advisor(
    message: str = Query(..., description="User query or strategy question"),
    symbol: Optional[str] = Query(None, description="Optional focus stock ticker"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    return StreamingResponse(
        stream_advisor_chat(
            message=message,
            symbol=symbol,
            user=current_user,
            db=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

