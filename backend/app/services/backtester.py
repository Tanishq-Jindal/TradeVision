import logging
import math
from typing import List
import numpy as np

from app.schemas.backtest import BacktestRequest, BacktestResult, BacktestTrade, EquityPoint
from app.services.indicators import calculate_macd, calculate_rsi, calculate_sma
from app.services.market_data import get_ohlcv

logger = logging.getLogger(__name__)


def parse_natural_language_strategy(prompt: str) -> tuple[str, dict]:
    """
    Parses natural language strategy descriptions into a parameterized strategy definition.
    """
    p = prompt.lower()
    params = {}

    if "rsi" in p:
        strat = "RSI_MOMENTUM"
        params["oversold"] = 30.0 if "30" in p else 35.0
        params["overbought"] = 70.0 if "70" in p else 65.0
    elif "macd" in p:
        strat = "MACD_MOMENTUM"
    elif "moving average" in p or "sma" in p or "cross" in p:
        strat = "SMA_CROSSOVER"
        params["fast_period"] = 10.0
        params["slow_period"] = 30.0
    else:
        strat = "RSI_MOMENTUM"
        params["oversold"] = 35.0
        params["overbought"] = 65.0

    return strat, params


async def run_backtest(req: BacktestRequest) -> BacktestResult:
    """
    Executes a bar-by-bar historical strategy simulation with comprehensive performance attribution.
    """
    sym = req.symbol.strip().upper()
    ohlcv = await get_ohlcv(sym, req.timeframe, req.bars_count)
    candles = ohlcv.candles

    if len(candles) < 30:
        return BacktestResult(
            symbol=sym,
            strategy_name=req.strategy_type,
            initial_cash=req.initial_cash,
            final_equity=req.initial_cash,
            total_return=0.0,
            total_return_pct=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            equity_curve=[EquityPoint(time=int(c.time), equity=req.initial_cash) for c in candles],
            trades=[],
        )

    # Strategy Resolution
    strategy_type = req.strategy_type
    params = req.params
    if req.strategy_prompt:
        parsed_type, parsed_params = parse_natural_language_strategy(req.strategy_prompt)
        strategy_type = parsed_type
        params.update(parsed_params)

    closes = [c.close for c in candles]
    times = [c.time for c in candles]
    n = len(closes)

    # Calculate indicators
    rsi = calculate_rsi(closes, 14)
    macd = calculate_macd(closes, 12, 26, 9)
    sma_fast = calculate_sma(closes, int(params.get("fast_period", 10)))
    sma_slow = calculate_sma(closes, int(params.get("slow_period", 30)))

    cash = req.initial_cash
    shares = 0.0
    entry_price = 0.0
    entry_time = 0

    trades: List[BacktestTrade] = []
    equity_curve: List[EquityPoint] = []
    daily_equities: List[float] = []

    oversold_thresh = params.get("oversold", 35.0)
    overbought_thresh = params.get("overbought", 65.0)

    for i in range(20, n):
        c_price = closes[i]
        bar_time = times[i]

        buy_signal = False
        sell_signal = False

        if strategy_type == "RSI_MOMENTUM":
            cur_rsi = rsi[i]
            if cur_rsi is not None:
                if cur_rsi < oversold_thresh and shares == 0:
                    buy_signal = True
                elif cur_rsi > overbought_thresh and shares > 0:
                    sell_signal = True

        elif strategy_type == "SMA_CROSSOVER":
            if (
                sma_fast[i] is not None
                and sma_slow[i] is not None
                and sma_fast[i - 1] is not None
                and sma_slow[i - 1] is not None
            ):
                if sma_fast[i] > sma_slow[i] and sma_fast[i - 1] <= sma_slow[i - 1] and shares == 0:
                    buy_signal = True
                elif sma_fast[i] < sma_slow[i] and sma_fast[i - 1] >= sma_slow[i - 1] and shares > 0:
                    sell_signal = True

        elif strategy_type == "MACD_MOMENTUM":
            cur_hist = macd["hist"][i]
            prev_hist = macd["hist"][i - 1]
            if cur_hist is not None and prev_hist is not None:
                if cur_hist > 0 and prev_hist <= 0 and shares == 0:
                    buy_signal = True
                elif cur_hist < 0 and prev_hist >= 0 and shares > 0:
                    sell_signal = True

        elif strategy_type == "BUY_AND_HOLD":
            if i == 20 and shares == 0:
                buy_signal = True

        # Execute Signals
        if buy_signal and cash > 0:
            shares = math.floor(cash / c_price)
            cash -= shares * c_price
            entry_price = c_price
            entry_time = bar_time

        elif sell_signal and shares > 0:
            proceeds = shares * c_price
            pnl = round(proceeds - (shares * entry_price), 2)
            pnl_pct = round(((c_price - entry_price) / entry_price) * 100, 2)
            trades.append(
                BacktestTrade(
                    symbol=sym,
                    entry_time=entry_time,
                    exit_time=bar_time,
                    side="BUY",
                    entry_price=entry_price,
                    exit_price=c_price,
                    shares=shares,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                )
            )
            cash += proceeds
            shares = 0.0

        current_equity = cash + (shares * c_price)
        equity_curve.append(EquityPoint(time=bar_time, equity=round(current_equity, 2)))
        daily_equities.append(current_equity)

    # Close any open trade at last bar price
    if shares > 0:
        c_price = closes[-1]
        proceeds = shares * c_price
        pnl = round(proceeds - (shares * entry_price), 2)
        pnl_pct = round(((c_price - entry_price) / entry_price) * 100, 2)
        trades.append(
            BacktestTrade(
                symbol=sym,
                entry_time=entry_time,
                exit_time=times[-1],
                side="BUY",
                entry_price=entry_price,
                exit_price=c_price,
                shares=shares,
                pnl=pnl,
                pnl_pct=pnl_pct,
            )
        )
        cash += proceeds
        shares = 0.0

    final_equity = round(cash, 2)
    total_return = round(final_equity - req.initial_cash, 2)
    total_return_pct = round((total_return / req.initial_cash) * 100, 2)

    # Risk & Win Rate Metrics
    eq_arr = np.array(daily_equities) if daily_equities else np.array([req.initial_cash])
    cum_max = np.maximum.accumulate(eq_arr)
    drawdowns = (eq_arr - cum_max) / cum_max
    max_dd = round(abs(float(np.min(drawdowns))) * 100, 2)

    returns = (eq_arr[1:] - eq_arr[:-1]) / eq_arr[:-1]
    std = float(np.std(returns)) if len(returns) > 1 else 0.01
    sharpe = round((float(np.mean(returns)) * 252 - 0.045) / (std * math.sqrt(252)), 2) if std > 0 else 0.0

    winning_trades = sum(1 for t in trades if t.pnl > 0)
    losing_trades = sum(1 for t in trades if t.pnl < 0)
    win_rate = round((winning_trades / len(trades)) * 100, 1) if trades else 0.0

    return BacktestResult(
        symbol=sym,
        strategy_name=f"{strategy_type} Strategy",
        initial_cash=req.initial_cash,
        final_equity=final_equity,
        total_return=total_return,
        total_return_pct=total_return_pct,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        win_rate=win_rate,
        total_trades=len(trades),
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        equity_curve=equity_curve,
        trades=trades,
    )
