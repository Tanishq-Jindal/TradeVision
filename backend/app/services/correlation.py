import logging
import time
from typing import Dict, List, Optional
import numpy as np
from app.schemas.correlation import CorrelationLink, CorrelationNode, CorrelationNetworkResponse
from app.services.market_data import UNIVERSE, get_ohlcv, get_quote

logger = logging.getLogger(__name__)


async def generate_correlation_network(symbols: Optional[List[str]] = None) -> CorrelationNetworkResponse:
    """
    Computes pairwise return correlation matrix and converts to a force-directed network graph.
    """
    selected_symbols = symbols or ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "PLTR", "JPM", "XOM"]

    nodes: List[CorrelationNode] = []
    returns_dict: Dict[str, np.ndarray] = {}

    for sym in selected_symbols:
        try:
            quote = await get_quote(sym)
            ohlcv = await get_ohlcv(sym, "1D", 60)
            meta = UNIVERSE.get(sym, {"name": sym, "sector": "Equities"})

            nodes.append(
                CorrelationNode(
                    id=sym,
                    name=meta["name"],
                    sector=meta["sector"],
                    price=quote.c,
                )
            )

            closes = np.array([c.close for c in ohlcv.candles])
            if len(closes) > 1:
                rets = (closes[1:] - closes[:-1]) / closes[:-1]
                returns_dict[sym] = rets
        except Exception as e:
            logger.warning(f"Error computing returns for {sym}: {str(e)}")

    # Compute Pairwise Pearson Correlation Links
    links: List[CorrelationLink] = []
    sym_keys = list(returns_dict.keys())

    for i in range(len(sym_keys)):
        for j in range(i + 1, len(sym_keys)):
            sym_a = sym_keys[i]
            sym_b = sym_keys[j]

            r_a = returns_dict[sym_a]
            r_b = returns_dict[sym_b]

            # Match lengths
            min_len = min(len(r_a), len(r_b))
            if min_len > 10:
                corr_matrix = np.corrcoef(r_a[-min_len:], r_b[-min_len:])
                corr_val = float(corr_matrix[0, 1])

                if not np.isnan(corr_val) and abs(corr_val) >= 0.25:
                    links.append(
                        CorrelationLink(
                            source=sym_a,
                            target=sym_b,
                            correlation=round(corr_val, 2),
                            weight=round(abs(corr_val), 2),
                        )
                    )

    return CorrelationNetworkResponse(
        nodes=nodes,
        links=links,
        timestamp=int(time.time()),
    )
