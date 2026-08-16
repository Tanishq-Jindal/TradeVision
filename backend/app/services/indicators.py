import math
from typing import Dict, List, Optional
import numpy as np


def calculate_sma(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculates Simple Moving Average (SMA) over a list of prices.
    Returns list of same length, with None for indices < period - 1.
    """
    n = len(prices)
    if n < period or period <= 0:
        return [None] * n

    result: List[Optional[float]] = [None] * (period - 1)
    current_sum = sum(prices[:period])
    result.append(round(current_sum / period, 4))

    for i in range(period, n):
        current_sum += prices[i] - prices[i - period]
        result.append(round(current_sum / period, 4))

    return result


def calculate_ema(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculates Exponential Moving Average (EMA).
    """
    n = len(prices)
    if n < period or period <= 0:
        return [None] * n

    result: List[Optional[float]] = [None] * (period - 1)
    # Seed with SMA
    sma = sum(prices[:period]) / period
    result.append(round(sma, 4))

    multiplier = 2.0 / (period + 1)
    current_ema = sma

    for i in range(period, n):
        current_ema = (prices[i] - current_ema) * multiplier + current_ema
        result.append(round(current_ema, 4))

    return result


def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculates Relative Strength Index (RSI) using Wilder's smoothed average method.
    """
    n = len(prices)
    if n <= period or period <= 0:
        return [None] * n

    deltas = [prices[i] - prices[i - 1] for i in range(1, n)]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    result: List[Optional[float]] = [None] * period

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
    result.append(round(rsi, 2))

    for i in range(period, len(deltas)):
        gain = gains[i]
        loss = losses[i]

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        result.append(round(rsi, 2))

    return result


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates MACD (Moving Average Convergence Divergence) Line, Signal Line, and Histogram.
    """
    n = len(prices)
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)

    macd_line: List[Optional[float]] = []
    for f, s in zip(fast_ema, slow_ema):
        if f is not None and s is not None:
            macd_line.append(round(f - s, 4))
        else:
            macd_line.append(None)

    # Filter out leading Nones to compute signal line
    valid_indices = [i for i, v in enumerate(macd_line) if v is not None]
    if len(valid_indices) < signal_period:
        return {
            "macd": macd_line,
            "signal": [None] * n,
            "hist": [None] * n,
        }

    first_valid = valid_indices[0]
    valid_macd_values = [macd_line[i] for i in valid_indices if macd_line[i] is not None] # type: ignore
    signal_sub = calculate_ema(valid_macd_values, signal_period)

    signal_line: List[Optional[float]] = [None] * first_valid + signal_sub
    hist_line: List[Optional[float]] = []

    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            hist_line.append(round(m - s, 4))
        else:
            hist_line.append(None)

    return {
        "macd": macd_line,
        "signal": signal_line,
        "hist": hist_line,
    }


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    num_std: float = 2.0,
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates Bollinger Bands (Upper, Middle, Lower).
    """
    n = len(prices)
    if n < period or period <= 0:
        return {
            "upper": [None] * n,
            "middle": [None] * n,
            "lower": [None] * n,
        }

    middle = calculate_sma(prices, period)
    upper: List[Optional[float]] = [None] * (period - 1)
    lower: List[Optional[float]] = [None] * (period - 1)

    for i in range(period - 1, n):
        window = prices[i - period + 1 : i + 1]
        std = np.std(window, ddof=0)
        mid = middle[i]
        if mid is not None:
            upper.append(round(mid + num_std * std, 4))
            lower.append(round(mid - num_std * std, 4))
        else:
            upper.append(None)
            lower.append(None)

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
    }


def calculate_momentum(prices: List[float], period: int = 10) -> List[Optional[float]]:
    """
    Calculates price momentum: (Price_t - Price_{t-n}) / Price_{t-n} * 100
    """
    n = len(prices)
    if n <= period or period <= 0:
        return [None] * n

    result: List[Optional[float]] = [None] * period
    for i in range(period, n):
        prev = prices[i - period]
        if prev != 0:
            result.append(round(((prices[i] - prev) / prev) * 100, 2))
        else:
            result.append(0.0)
    return result


def calculate_volume_ratio(volumes: List[float], period: int = 20) -> List[Optional[float]]:
    """
    Calculates Volume Ratio: Volume_t / SMA(Volume, period)
    """
    n = len(volumes)
    vol_sma = calculate_sma(volumes, period)
    result: List[Optional[float]] = []

    for v, s in zip(volumes, vol_sma):
        if s is not None and s > 0:
            result.append(round(v / s, 2))
        else:
            result.append(None)
    return result
