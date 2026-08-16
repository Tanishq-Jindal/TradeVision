from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    symbol: str
    direction: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    probability: float = Field(..., ge=0.0, le=1.0, description="Predicted probability of positive return")
    confidence: str = Field(..., description="HIGH, MEDIUM, or LOW")
    horizon: str = "24h"
    features_importance: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "v1.0-ensemble"
    timestamp: int


class SentimentArticleScore(BaseModel):
    id: str
    headline: str
    summary: str
    source: str
    score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score (-1.0 to +1.0)")
    label: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    url: str
    datetime: int


class SentimentResponse(BaseModel):
    symbol: str
    overall_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str = Field(..., description="VERY_BULLISH, BULLISH, NEUTRAL, BEARISH, VERY_BEARISH")
    bullish_pct: float
    bearish_pct: float
    neutral_pct: float
    articles: List[SentimentArticleScore]
    summary_insight: str
    timestamp: int


class ChatMessage(BaseModel):
    role: str = Field(..., description="user, model, or system")
    content: str


class AdvisorChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    symbol: Optional[str] = None


class RiskMetricResponse(BaseModel):
    symbol_or_portfolio: str
    annualized_volatility: float
    var_95: float = Field(..., description="1-day 95% Value at Risk ($)")
    cvar_95: float = Field(..., description="1-day 95% Conditional Value at Risk ($)")
    max_drawdown: float = Field(..., description="Historical Maximum Drawdown (%)")
    sharpe_ratio: float
    monte_carlo_simulations: int = 10000
    monte_carlo_95_ci_lower: float
    monte_carlo_95_ci_upper: float
    concentration_hhi: float
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, EXTREME")
    timestamp: int


class SignalScanItem(BaseModel):
    id: str
    symbol: str
    name: str
    signal_type: str = Field(..., description="STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL")
    composite_score: float = Field(..., ge=0.0, le=100.0)
    technical_score: float
    ml_prediction_score: float
    sentiment_score: float
    price: float
    change_pct: float
    key_drivers: List[str]
    generated_at: int
