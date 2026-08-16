# TradeWise

> Full-stack, AI-assisted paper trading and portfolio intelligence platform.
> Built for III 5.0 Hackathon.

TradeWise provides quantitative learners and retail traders with a unified, professional trading intelligence workflow:
```
Market Data → ML Directional Predictions → Sentiment Analysis → Multi-Agent Swarm → Risk Analytics → Paper Execution → Natural Language Backtesting
```

---

## Key Features & Platform Capabilities

### 1. Paper Trading Engine ($100k Virtual Portfolio)
- **Virtual Cash Balance**: Every user account is initialized with **$100,000.00 virtual cash**.
- **Atomic Trade Execution**: Row-locked (`FOR UPDATE`) order processing prevents concurrent double-spending.
- **Mark-to-Market Valuation**: Real-time position tracking with live unrealized P&L, weighted average entry prices, and general ledger audit transactions.

### 2. Multi-Tier Market Data & Simulation Fallback
- **Tier 1 (Memory)**: 5s–10s fast in-memory quote caching.
- **Tier 2 (Redis)**: Distributed caching across quotes, OHLCV bars, and news.
- **Tier 3 (Finnhub API & Simulator)**: Live US equities market quotes with realistic Geometric Brownian Motion random-walk simulation when markets are closed or offline.
- **Real-Time Streaming**: Server-Sent Events (SSE) `/api/v1/market/stream`.

### 3. Layered AI & Quantitative Intelligence
- **ML Price-Direction Predictions (`/api/v1/ai/prediction/{symbol}`)**: Ensemble classification (Logistic Regression + Random Forest) over technical indicators (RSI, MACD, Bollinger %B, Momentum, SMA ratios) with feature importance attribution.
- **Financial News Sentiment (`/api/v1/ai/sentiment/{symbol}`)**: Domain-specific sentiment scoring across live financial headlines with bullish/bearish breakdown.
- **Multi-Agent Swarm Deliberation (`/api/v1/swarm/{symbol}`)**: 4 specialized financial agents:
  - *Momentum & Trend Agent* (price velocity & breakout trend)
  - *Mean Reversion Agent* (statistical oscillator extremes)
  - *Sentiment & Narrative Agent* (institutional headline tone)
  - *Risk & Capital Guardrail Agent* (volatility bounds & position size limits)
- **Conversational AI Advisor (`/api/v1/ai/advisor/stream`)**: Streaming quantitative assistant with live tool synthesis.
- **Portfolio Risk Engine & Monte Carlo (`/api/v1/ai/risk/*`)**: Annualized volatility, 95% 1-day Value at Risk (VaR), Conditional VaR (CVaR), Maximum Drawdown, Sharpe ratio, and **10,000-simulation 30-day Monte Carlo projection bounds**.
- **Autonomous Signal Scanner (`/api/v1/ai/signals/active`)**: Multi-factor opportunity screener ranking trade setups by composite technical, ML, and sentiment scores.

### 4. Advanced Autonomous & Interactive Tools
- **Natural Language Backtesting (`/api/v1/backtest/run`)**: Convert plain English strategies (e.g. *"Buy when RSI is below 30 and sell when above 70"*) into bar-by-bar simulations with win rate, Sharpe ratio, max drawdown, and equity curves.
- **Command Palette (`Ctrl+K` / `/api/v1/command/parse`)**: Fast natural language trading and navigation (e.g. *"Buy 20 shares of NVDA"*).
- **Guardrailed Autopilot (`/api/v1/autopilot/*`)**: Automated trading with user-defined stop-loss %, take-profit %, max allocation limits, and autonomous audit logs.
- **Cross-Asset Correlation Network (`/api/v1/correlation/network`)**: Pairwise return correlation matrix for portfolio diversification analysis.

---

## Demo Account Credentials

For instant platform testing and evaluation:
- **Email:** `demo@tradewise.cloud`
- **Password:** `demo123`
- **Starting Portfolio:** `$100,000.00` virtual cash

---

## Architecture & Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, TradingView Lightweight Charts, Lucide Icons |
| **Backend** | FastAPI (Python 3.12+), Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Uvicorn |
| **Data & Cache** | PostgreSQL 16, Redis 7 (`redis.asyncio`), In-Memory L1 Cache |
| **Analytics & ML** | NumPy, Pandas, Scikit-Learn |
| **Orchestration** | Docker, Docker Compose |

---

## Quickstart

### 1. Docker Compose (One-Command Launch)
```bash
docker compose up --build
```
- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Probes:** [http://localhost:8000/health](http://localhost:8000/health)

### 2. Local Development Setup

#### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Running Automated Tests (41/41 Tests)
```bash
cd backend
.\.venv\Scripts\python -m pytest -v
```
