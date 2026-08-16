import re
from typing import Optional
from app.schemas.command import CommandParseRequest, CommandParseResponse
from app.services.market_data import UNIVERSE, get_quote


async def parse_trade_command(cmd_req: CommandParseRequest) -> CommandParseResponse:
    """
    Parses natural language commands from the UI command palette (Ctrl+K).
    """
    raw = cmd_req.command.strip()
    lower_cmd = raw.lower()

    # Detect Symbol
    detected_symbol: Optional[str] = None
    words = re.findall(r"\b[A-Za-z0-9]+\b", raw)

    # Check for known symbol in UNIVERSE
    for w in words:
        upper_w = w.upper()
        if upper_w in UNIVERSE:
            detected_symbol = upper_w
            break

    # Detect Quantity (numbers)
    detected_qty: Optional[float] = None
    num_matches = re.findall(r"\b\d+(?:\.\d+)?\b", raw)
    if num_matches:
        detected_qty = float(num_matches[0])

    # 1. Buy Order Intent
    if any(k in lower_cmd for k in ["buy", "purchase", "long"]) and detected_symbol:
        qty = detected_qty or 10.0
        quote = await get_quote(detected_symbol)
        total = round(qty * quote.c, 2)

        return CommandParseResponse(
            raw_command=raw,
            action="TRADE_BUY",
            symbol=detected_symbol,
            quantity=qty,
            estimated_price=quote.c,
            estimated_total=total,
            requires_confirmation=True,
            preview_message=f"Confirm BUY order for {qty:g} shares of {detected_symbol} @ ~${quote.c:.2f} (~${total:,.2f} total)?",
        )

    # 2. Sell Order Intent
    if any(k in lower_cmd for k in ["sell", "short", "dump", "close"]) and detected_symbol:
        qty = detected_qty or 10.0
        quote = await get_quote(detected_symbol)
        total = round(qty * quote.c, 2)

        return CommandParseResponse(
            raw_command=raw,
            action="TRADE_SELL",
            symbol=detected_symbol,
            quantity=qty,
            estimated_price=quote.c,
            estimated_total=total,
            requires_confirmation=True,
            preview_message=f"Confirm SELL order for {qty:g} shares of {detected_symbol} @ ~${quote.c:.2f} (~${total:,.2f} total)?",
        )

    # 3. Add to Watchlist Intent
    if any(k in lower_cmd for k in ["watchlist", "watch", "track", "bookmark"]) and detected_symbol:
        return CommandParseResponse(
            raw_command=raw,
            action="ADD_WATCHLIST",
            symbol=detected_symbol,
            requires_confirmation=False,
            preview_message=f"Add {detected_symbol} to your active watchlist.",
        )

    # 4. Backtest Intent
    if any(k in lower_cmd for k in ["backtest", "simulate", "strategy"]) and detected_symbol:
        return CommandParseResponse(
            raw_command=raw,
            action="RUN_BACKTEST",
            symbol=detected_symbol,
            requires_confirmation=False,
            preview_message=f"Run strategy backtest on {detected_symbol}.",
        )

    # 5. View Risk Intent
    if any(k in lower_cmd for k in ["risk", "var", "volatility"]) and detected_symbol:
        return CommandParseResponse(
            raw_command=raw,
            action="VIEW_RISK",
            symbol=detected_symbol,
            requires_confirmation=False,
            preview_message=f"Inspect portfolio risk analytics for {detected_symbol}.",
        )

    # 6. Navigate Symbol Intent
    if detected_symbol:
        return CommandParseResponse(
            raw_command=raw,
            action="NAVIGATE_SYMBOL",
            symbol=detected_symbol,
            requires_confirmation=False,
            preview_message=f"Load chart and market overview for {detected_symbol}.",
        )

    return CommandParseResponse(
        raw_command=raw,
        action="UNKNOWN",
        requires_confirmation=False,
        preview_message="Unrecognized command. Try 'Buy 10 NVDA', 'Sell 5 AAPL', or 'Watch TSLA'.",
    )
