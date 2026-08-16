import logging
import math
import time
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.autopilot import AutopilotAction, AutopilotConfig, AutopilotStatusResponse
from app.schemas.trading import TradeOrderRequest
from app.services.market_data import get_quote
from app.services.scanner import scan_market_signals
from app.services.swarm import generate_swarm_consensus
from app.services.trading_engine import execute_buy, execute_sell, get_or_create_portfolio, get_user_positions

logger = logging.getLogger(__name__)

# In-memory config store per user
_user_autopilot_configs: Dict[int, AutopilotConfig] = {}
_user_autopilot_logs: Dict[int, List[AutopilotAction]] = {}


def get_user_autopilot_config(user_id: int) -> AutopilotConfig:
    return _user_autopilot_configs.get(user_id, AutopilotConfig())


def update_user_autopilot_config(user_id: int, cfg: AutopilotConfig) -> AutopilotConfig:
    _user_autopilot_configs[user_id] = cfg
    return cfg


async def evaluate_and_run_autopilot_cycle(db: AsyncSession, user_id: int) -> AutopilotStatusResponse:
    """
    Evaluates risk limits, take-profit/stop-loss triggers, and swarm opportunities for autonomous paper trade execution.
    """
    cfg = get_user_autopilot_config(user_id)
    actions: List[AutopilotAction] = _user_autopilot_logs.get(user_id, [])

    if not cfg.enabled:
        return AutopilotStatusResponse(
            config=cfg,
            active=False,
            recent_actions=actions[:10],
            last_evaluated_at=int(time.time()),
        )

    portfolio = await get_or_create_portfolio(db, user_id)
    positions = await get_user_positions(db, user_id)
    now = int(time.time())

    # 1. Evaluate open positions for Stop-Loss or Take-Profit
    for pos in positions:
        quote = await get_quote(pos.symbol)
        pnl_pct = pos.unrealized_pnl_pct

        # Stop-Loss trigger
        if pnl_pct <= -cfg.stop_loss_pct:
            try:
                order = TradeOrderRequest(symbol=pos.symbol, quantity=pos.quantity, price=quote.c)
                await execute_sell(db, user_id, order)
                action = AutopilotAction(
                    action_type="AUTONOMOUS_SELL_STOP_LOSS",
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    price=quote.c,
                    reason=f"Hit stop-loss cutoff ({pnl_pct:.2f}% <= -{cfg.stop_loss_pct}%). Protected capital.",
                    timestamp=now,
                )
                actions.insert(0, action)
            except Exception as e:
                logger.error(f"Autopilot sell error on {pos.symbol}: {str(e)}")

        # Take-Profit trigger
        elif pnl_pct >= cfg.take_profit_pct:
            try:
                order = TradeOrderRequest(symbol=pos.symbol, quantity=pos.quantity, price=quote.c)
                await execute_sell(db, user_id, order)
                action = AutopilotAction(
                    action_type="AUTONOMOUS_SELL_TAKE_PROFIT",
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    price=quote.c,
                    reason=f"Hit take-profit target (+{pnl_pct:.2f}% >= +{cfg.take_profit_pct}%). Locked in gains.",
                    timestamp=now,
                )
                actions.insert(0, action)
            except Exception as e:
                logger.error(f"Autopilot sell error on {pos.symbol}: {str(e)}")

    # 2. Evaluate high-conviction buy opportunities if cash is available
    cash_available = float(portfolio.cash_balance)
    if cash_available > 500.0:
        signals = await scan_market_signals(top_n=3)
        for sig in signals:
            if sig.signal_type in ["STRONG_BUY", "BUY"] and sig.composite_score >= (cfg.min_confidence_threshold * 100):
                # Check if already holding
                if any(p.symbol == sig.symbol for p in positions):
                    continue

                quote = await get_quote(sig.symbol)
                max_dollar_alloc = (cfg.max_trade_allocation_pct / 100.0) * cash_available
                shares_to_buy = math.floor(max_dollar_alloc / quote.c)

                if shares_to_buy > 0:
                    try:
                        order = TradeOrderRequest(symbol=sig.symbol, quantity=shares_to_buy, price=quote.c)
                        await execute_buy(db, user_id, order)
                        action = AutopilotAction(
                            action_type="AUTONOMOUS_BUY_OPPORTUNITY",
                            symbol=sig.symbol,
                            quantity=shares_to_buy,
                            price=quote.c,
                            reason=f"Swarm composite score {sig.composite_score:.1f}/100. Drivers: {', '.join(sig.key_drivers[:2])}",
                            timestamp=now,
                        )
                        actions.insert(0, action)
                        cash_available -= shares_to_buy * quote.c
                    except Exception as e:
                        logger.error(f"Autopilot buy error on {sig.symbol}: {str(e)}")

    _user_autopilot_logs[user_id] = actions

    return AutopilotStatusResponse(
        config=cfg,
        active=cfg.enabled,
        recent_actions=actions[:10],
        last_evaluated_at=now,
    )
