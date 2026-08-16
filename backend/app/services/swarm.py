import logging
import time
from typing import List
from app.schemas.swarm import AgentOpinion, SwarmConsensusResponse
from app.services.indicators import calculate_bollinger_bands, calculate_momentum, calculate_rsi
from app.services.market_data import get_ohlcv, get_quote
from app.services.prediction import predict_price_direction
from app.services.risk import calculate_symbol_risk
from app.services.sentiment import analyze_symbol_sentiment

logger = logging.getLogger(__name__)


async def generate_swarm_consensus(symbol: str) -> SwarmConsensusResponse:
    """
    Executes a 4-agent consensus deliberation for a specific stock ticker.
    """
    sym = symbol.strip().upper()
    quote = await get_quote(sym)
    ohlcv = await get_ohlcv(sym, "1D", 80)
    pred = await predict_price_direction(sym)
    sent = await analyze_symbol_sentiment(sym)
    risk = await calculate_symbol_risk(sym)

    closes = [c.close for c in ohlcv.candles]
    rsi = calculate_rsi(closes, 14)
    mom_10 = calculate_momentum(closes, 10)
    bb = calculate_bollinger_bands(closes, 20)

    latest_rsi = rsi[-1] if rsi and rsi[-1] is not None else 50.0
    latest_mom = mom_10[-1] if mom_10 and mom_10[-1] is not None else 0.0
    c_price = closes[-1] if closes else quote.c

    agents: List[AgentOpinion] = []

    # Agent 1: Trend & Momentum Agent
    if latest_mom > 3.0:
        a1_sig = "BULLISH"
        a1_conf = 0.85
        a1_reason = f"Strong positive 10-day velocity (+{latest_mom:.1f}%) and solid upward breakout trend."
    elif latest_mom < -3.0:
        a1_sig = "BEARISH"
        a1_conf = 0.80
        a1_reason = f"Negative price momentum (-{abs(latest_mom):.1f}%) reflecting sustained selling pressure."
    else:
        a1_sig = "NEUTRAL"
        a1_conf = 0.60
        a1_reason = "Price is consolidating within a narrow consolidation band with flat momentum."

    agents.append(
        AgentOpinion(
            agent_name="Momentum & Trend Agent",
            role="Trend Velocity Analyst",
            signal=a1_sig,
            confidence=a1_conf,
            reasoning=a1_reason,
            recommended_weight=0.30,
        )
    )

    # Agent 2: Statistical Mean Reversion Agent
    if latest_rsi < 35:
        a2_sig = "BULLISH"
        a2_conf = 0.88
        a2_reason = f"RSI is oversold at {latest_rsi:.1f}, indicating high statistical probability of mean reversion bounce."
    elif latest_rsi > 65:
        a2_sig = "BEARISH"
        a2_conf = 0.85
        a2_reason = f"RSI is extended in overbought territory at {latest_rsi:.1f}; elevated probability of mean reversion pullback."
    else:
        a2_sig = "NEUTRAL"
        a2_conf = 0.65
        a2_reason = f"RSI ({latest_rsi:.1f}) is balanced near equilibrium; no mean reversion extremes present."

    agents.append(
        AgentOpinion(
            agent_name="Mean Reversion Agent",
            role="Statistical Oscillator Specialist",
            signal=a2_sig,
            confidence=a2_conf,
            reasoning=a2_reason,
            recommended_weight=0.25,
        )
    )

    # Agent 3: Sentiment & Narrative Agent
    if sent.overall_score >= 0.20:
        a3_sig = "BULLISH"
        a3_conf = min(0.95, 0.60 + abs(sent.overall_score) * 0.4)
        a3_reason = f"Institutional news headlines are {sent.bullish_pct}% positive. Core narrative: {sent.summary_insight}"
    elif sent.overall_score <= -0.20:
        a3_sig = "BEARISH"
        a3_conf = min(0.95, 0.60 + abs(sent.overall_score) * 0.4)
        a3_reason = f"Media coverage reflects {sent.bearish_pct}% bearish headlines with active headwind commentary."
    else:
        a3_sig = "NEUTRAL"
        a3_conf = 0.60
        a3_reason = "News headlines are evenly balanced with neutral market perception."

    agents.append(
        AgentOpinion(
            agent_name="Sentiment & Narrative Agent",
            role="News Sentiment Specialist",
            signal=a3_sig,
            confidence=a3_conf,
            reasoning=a3_reason,
            recommended_weight=0.25,
        )
    )

    # Agent 4: Risk & Allocation Guardrail Agent
    max_alloc_pct = 20.0
    if risk.annualized_volatility > 40.0 or risk.risk_level == "HIGH":
        max_alloc_pct = 8.0
        a4_sig = "BEARISH" if pred.direction == "BEARISH" else "NEUTRAL"
        a4_conf = 0.85
        a4_reason = f"Elevated volatility ({risk.annualized_volatility:.1f}%) and 95% VaR of ${risk.var_95:,.2f}. Recommend capping position size at {max_alloc_pct}%."
    elif risk.risk_level == "LOW":
        max_alloc_pct = 25.0
        a4_sig = "BULLISH" if pred.direction == "BULLISH" else "NEUTRAL"
        a4_conf = 0.75
        a4_reason = f"Stable risk profile ({risk.annualized_volatility:.1f}% vol, Sharpe {risk.sharpe_ratio:.2f}). Safe for standard allocations up to {max_alloc_pct}%."
    else:
        max_alloc_pct = 15.0
        a4_sig = "NEUTRAL"
        a4_conf = 0.70
        a4_reason = f"Moderate risk parameters ({risk.annualized_volatility:.1f}% vol). Standard {max_alloc_pct}% position cap advised."

    agents.append(
        AgentOpinion(
            agent_name="Risk & Capital Guardrail Agent",
            role="Portfolio Risk Officer",
            signal=a4_sig,
            confidence=a4_conf,
            reasoning=a4_reason,
            recommended_weight=0.20,
        )
    )

    # Consensus Computation
    sig_values = {"BULLISH": 1.0, "NEUTRAL": 0.0, "BEARISH": -1.0}
    weighted_score = sum(sig_values[a.signal] * a.confidence * a.recommended_weight for a in agents)
    weighted_score = round(max(-1.0, min(1.0, weighted_score)), 2)

    # Agreement percentage
    signals_list = [a.signal for a in agents]
    most_common_count = max(signals_list.count("BULLISH"), signals_list.count("BEARISH"), signals_list.count("NEUTRAL"))
    agreement_pct = round((most_common_count / len(agents)) * 100, 1)

    if weighted_score >= 0.50:
        consensus_sig = "STRONG_BUY"
        summary = f"Multi-Agent Swarm exhibits strong bullish consensus (+{weighted_score:.2f}) across trend, sentiment, and ML signals."
    elif weighted_score >= 0.18:
        consensus_sig = "BUY"
        summary = f"Consensus leans constructive (+{weighted_score:.2f}) with majority agent agreement."
    elif weighted_score <= -0.50:
        consensus_sig = "STRONG_SELL"
        summary = f"Multi-Agent Swarm projects strong bearish agreement ({weighted_score:.2f}) with compounding downside factors."
    elif weighted_score <= -0.18:
        consensus_sig = "SELL"
        summary = f"Consensus is defensive ({weighted_score:.2f}) citing adverse momentum or news sentiment."
    else:
        consensus_sig = "NEUTRAL"
        summary = f"Agents are in mixed deadlock ({weighted_score:.2f}). Market forces appear balanced without a definitive trend trigger."

    return SwarmConsensusResponse(
        symbol=sym,
        consensus_signal=consensus_sig,
        consensus_score=weighted_score,
        agreement_percentage=agreement_pct,
        max_position_size_pct=max_alloc_pct,
        summary=summary,
        agents=agents,
        timestamp=int(time.time()),
    )
