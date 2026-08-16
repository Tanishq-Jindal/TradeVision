import logging
import re
import time
from typing import List
from app.schemas.ai import SentimentArticleScore, SentimentResponse
from app.services.market_data import get_news

logger = logging.getLogger(__name__)

# Financial Sentiment Lexicon
BULLISH_KEYWORDS = {
    "growth", "surge", "expand", "profit", "bullish", "record", "upgrade", "outperform",
    "beat", "solid", "strong", "gains", "dividend", "revenue", "breakthrough", "rally",
    "positive", "adoption", "momentum", "buyback", "milestone", "higher", "partnership"
}

BEARISH_KEYWORDS = {
    "drop", "fall", "decline", "bearish", "loss", "downgrade", "underperform", "miss",
    "weak", "slump", "investigation", "lawsuit", "debt", "risk", "warning", "layoffs",
    "inflation", "recession", "concern", "plunge", "lower", "headwind", "deficit"
}


def score_text_financial_sentiment(text: str) -> float:
    """
    Computes financial domain sentiment score between -1.0 and +1.0 using domain lexicon.
    """
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        return 0.0

    pos_count = sum(1 for w in words if w in BULLISH_KEYWORDS)
    neg_count = sum(1 for w in words if w in BEARISH_KEYWORDS)

    total_matched = pos_count + neg_count
    if total_matched == 0:
        return 0.05  # Slight baseline neutral optimism in financial markets

    raw_score = (pos_count - neg_count) / total_matched
    return round(float(raw_score), 2)


async def analyze_symbol_sentiment(symbol: str) -> SentimentResponse:
    """
    Analyzes sentiment across recent financial news articles for a symbol.
    """
    sym = symbol.strip().upper()
    articles = await get_news(sym)

    scored_articles: List[SentimentArticleScore] = []
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    scores: List[float] = []

    for art in articles:
        combined_text = f"{art.headline} {art.summary}"
        score = score_text_financial_sentiment(combined_text)
        scores.append(score)

        if score >= 0.20:
            label = "BULLISH"
            bullish_count += 1
        elif score <= -0.20:
            label = "BEARISH"
            bearish_count += 1
        else:
            label = "NEUTRAL"
            neutral_count += 1

        scored_articles.append(
            SentimentArticleScore(
                id=art.id,
                headline=art.headline,
                summary=art.summary,
                source=art.source,
                score=score,
                label=label,
                url=art.url,
                datetime=art.datetime,
            )
        )

    total_articles = len(articles) if articles else 1
    bullish_pct = round((bullish_count / total_articles) * 100, 1)
    bearish_pct = round((bearish_count / total_articles) * 100, 1)
    neutral_pct = round((neutral_count / total_articles) * 100, 1)

    overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    if overall_score >= 0.40:
        sentiment_label = "VERY_BULLISH"
        insight = f"Institutional news sentiment for {sym} is distinctly bullish, driven by strong earnings signals and operational expansion."
    elif overall_score >= 0.15:
        sentiment_label = "BULLISH"
        insight = f"Market coverage for {sym} leans constructive with steady positive analyst commentary."
    elif overall_score <= -0.40:
        sentiment_label = "VERY_BEARISH"
        insight = f"Recent news headlines for {sym} are dominated by adverse headwinds and defensive sentiment."
    elif overall_score <= -0.15:
        sentiment_label = "BEARISH"
        insight = f"Media sentiment for {sym} reflects near-term caution and profit-taking concerns."
    else:
        sentiment_label = "NEUTRAL"
        insight = f"News sentiment for {sym} remains balanced with no single dominant macroeconomic directional driver."

    return SentimentResponse(
        symbol=sym,
        overall_score=overall_score,
        sentiment_label=sentiment_label,
        bullish_pct=bullish_pct,
        bearish_pct=bearish_pct,
        neutral_pct=neutral_pct,
        articles=scored_articles,
        summary_insight=insight,
        timestamp=int(time.time()),
    )
