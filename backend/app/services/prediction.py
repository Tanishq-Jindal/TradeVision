import logging
import math
import time
from typing import Dict, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from app.schemas.ai import PredictionResponse
from app.services.indicators import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_momentum,
    calculate_rsi,
    calculate_sma,
    calculate_volume_ratio,
)
from app.services.market_data import get_ohlcv

logger = logging.getLogger(__name__)


def extract_features_and_labels(candles: list):
    """
    Transforms raw OHLCV bars into a normalized feature matrix and forward return targets.
    """
    closes = [c.close for c in candles]
    volumes = [float(c.volume) for c in candles]
    n = len(closes)

    if n < 40:
        return None, None, None

    rsi = calculate_rsi(closes, 14)
    macd_res = calculate_macd(closes, 12, 26, 9)
    macd_hist = macd_res["hist"]
    bb_res = calculate_bollinger_bands(closes, 20)
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    mom_10 = calculate_momentum(closes, 10)
    vol_ratio = calculate_volume_ratio(volumes, 20)

    X = []
    y = []

    # Features: [rsi/100, macd_hist/close, (close-bb_lower)/(bb_upper-bb_lower), mom_10/100, close/sma_20 - 1, vol_ratio]
    feature_names = [
        "RSI (14)",
        "MACD Histogram",
        "Bollinger %B",
        "10-Day Momentum",
        "SMA 20 Distance",
        "Volume Ratio",
    ]

    for i in range(30, n - 1):
        if (
            rsi[i] is not None
            and macd_hist[i] is not None
            and bb_res["upper"][i] is not None
            and bb_res["lower"][i] is not None
            and sma_20[i] is not None
            and mom_10[i] is not None
            and vol_ratio[i] is not None
        ):
            c_price = closes[i]
            bb_width = bb_res["upper"][i] - bb_res["lower"][i]
            bb_pct = (c_price - bb_res["lower"][i]) / bb_width if bb_width > 0 else 0.5
            sma_dist = (c_price / sma_20[i]) - 1.0

            feats = [
                rsi[i] / 100.0,
                macd_hist[i] / c_price,
                bb_pct,
                mom_10[i] / 100.0,
                sma_dist,
                min(vol_ratio[i], 5.0) / 5.0,
            ]
            X.append(feats)

            # Target: 1 if next day close > current close else 0
            next_ret = closes[i + 1] - closes[i]
            y.append(1 if next_ret > 0 else 0)

    # Current latest feature vector for inference
    latest_idx = n - 1
    c_price = closes[latest_idx]
    bb_width = (bb_res["upper"][latest_idx] or c_price) - (bb_res["lower"][latest_idx] or c_price)
    bb_pct = (c_price - (bb_res["lower"][latest_idx] or c_price)) / bb_width if bb_width > 0 else 0.5
    sma_dist = (c_price / (sma_20[latest_idx] or c_price)) - 1.0

    latest_X = [
        (rsi[latest_idx] or 50.0) / 100.0,
        (macd_hist[latest_idx] or 0.0) / c_price,
        bb_pct,
        (mom_10[latest_idx] or 0.0) / 100.0,
        sma_dist,
        min(vol_ratio[latest_idx] or 1.0, 5.0) / 5.0,
    ]

    return np.array(X), np.array(y), np.array([latest_X]), feature_names


async def predict_price_direction(symbol: str) -> PredictionResponse:
    """
    Generates an ML price direction prediction (Bullish/Bearish/Neutral) with confidence and feature importances.
    """
    sym = symbol.strip().upper()
    ohlcv = await get_ohlcv(sym, "1D", 120)

    if len(ohlcv.candles) < 40:
        return PredictionResponse(
            symbol=sym,
            direction="NEUTRAL",
            probability=0.50,
            confidence="LOW",
            features_importance={},
            timestamp=int(time.time()),
        )

    X, y, latest_X, feature_names = extract_features_and_labels(ohlcv.candles)

    if X is None or len(X) < 15:
        return PredictionResponse(
            symbol=sym,
            direction="NEUTRAL",
            probability=0.50,
            confidence="LOW",
            features_importance={},
            timestamp=int(time.time()),
        )

    # Train ensemble (Logistic Regression + Random Forest)
    lr = LogisticRegression(C=1.0, max_iter=200)
    rf = RandomForestClassifier(n_estimators=30, max_depth=4, random_state=42)

    lr.fit(X, y)
    rf.fit(X, y)

    prob_lr = float(lr.predict_proba(latest_X)[0][1])
    prob_rf = float(rf.predict_proba(latest_X)[0][1])

    # Ensemble probability (weighted average)
    prob = round((0.4 * prob_lr + 0.6 * prob_rf), 2)

    if prob >= 0.55:
        direction = "BULLISH"
    elif prob <= 0.45:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"

    # Confidence calculation
    distance = abs(prob - 0.5)
    if distance >= 0.18:
        confidence = "HIGH"
    elif distance >= 0.08:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Feature importances from Random Forest
    rf_importances = rf.feature_importances_
    features_importance = {
        name: round(float(imp), 3)
        for name, imp in zip(feature_names, rf_importances)
    }

    return PredictionResponse(
        symbol=sym,
        direction=direction,
        probability=prob,
        confidence=confidence,
        horizon="24h",
        features_importance=features_importance,
        model_version="v1.0-ensemble",
        timestamp=int(time.time()),
    )
