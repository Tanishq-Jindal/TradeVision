import {
  HealthResponse,
  ApiErrorEnvelope,
  User,
  AuthResponse,
  LoginInput,
  RegisterInput,
  Quote,
  SymbolSearchResult,
  OHLCVData,
  NewsArticle,
  OrderInput,
  Trade,
  Position,
  Transaction,
  PortfolioResponse,
  PortfolioSummary,
  WatchlistItem,
  Watchlist,
  PredictionResponse,
  SentimentResponse,
  RiskMetricResponse,
  SignalScanItem,
  SwarmConsensusResponse,
  BacktestResult,
  CommandParseResponse,
  AutopilotStatusResponse,
  AutopilotConfig,
  CorrelationNetworkResponse,
const TOKEN_KEY = "tradevision_access_token";

export function getStoredToken(): string | null {
  if (typeof window !== "undefined") {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }
  return null;
}

export function setStoredToken(token: string | null): void {
  if (typeof window !== "undefined") {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch {
      // Ignore localStorage errors (e.g. private browsing quota)
    }
  }
}

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const custom = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (custom && custom.trim() && !custom.includes("<") && !custom.includes(">")) {
      let url = custom.trim().replace(/\/+$/, "");
      if (window.location.hostname === "127.0.0.1" && url.includes("localhost")) {
        url = url.replace("localhost", "127.0.0.1");
      }
      if (window.location.hostname === "localhost" && url.includes("127.0.0.1")) {
        url = url.replace("127.0.0.1", "localhost");
      }
      // Guarantee /api/v1 suffix if omitted
      if (!url.endsWith("/api/v1")) {
        url = `${url}/api/v1`;
      }
      return url;
    }
    // If running in local dev on localhost or 127.0.0.1
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return `http://${window.location.hostname}:8000/api/v1`;
    }
    // If deployed on cloud/Vercel and NEXT_PUBLIC_API_BASE_URL was omitted, fallback to origin /api/v1
    return `${window.location.origin}/api/v1`;
  }
  let fallback = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1").trim().replace(/\/+$/, "");
  if (!fallback.endsWith("/api/v1")) {
    fallback = `${fallback}/api/v1`;
  }
  return fallback;
}

export const API_BASE_URL = getApiBaseUrl();

export class ApiError extends Error {
  code: string;
  details?: Record<string, any>;
  statusCode: number;

  constructor(code: string, message: string, statusCode: number, details?: Record<string, any>) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getApiBaseUrl();
  let url = endpoint.startsWith("http")
    ? endpoint
    : `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  const token = getStoredToken();
  if (token) {
    defaultHeaders["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      if (data && data.error) {
        const err = data as ApiErrorEnvelope;
        throw new ApiError(
          err.error.code || "API_ERROR",
          err.error.message || "An unexpected error occurred",
          response.status,
          err.error.details
        );
      }
      throw new ApiError(
        `HTTP_${response.status}`,
        response.statusText || "Request failed",
        response.status
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (typeof window !== "undefined") {
      console.error(`[API Network Error] ${options.method || "GET"} ${url}:`, error);
    }
    throw new ApiError(
      "NETWORK_ERROR",
      error instanceof Error ? error.message : "Unable to reach the server",
      0
    );
  }
}

export const api = {
  // Health
  getHealth: async (): Promise<HealthResponse> => {
    try {
      return await request<HealthResponse>("/health");
    } catch {
      const rootUrl = API_BASE_URL.replace(/\/api\/v1\/?$/, "") + "/health";
      return await request<HealthResponse>(rootUrl);
    }
  },

  // Auth
  register: async (input: RegisterInput): Promise<AuthResponse> => {
    const res = await request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    });
    if (res.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  login: async (input: LoginInput): Promise<AuthResponse> => {
    const res = await request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    });
    if (res.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  getMe: async (): Promise<User> => {
    return await request<User>("/auth/me", {
      method: "GET",
    });
  },

  logout: async (): Promise<{ message: string }> => {
    try {
      return await request<{ message: string }>("/auth/logout", {
        method: "POST",
      });
    } finally {
      setStoredToken(null);
    }
  },

  // Market Data
  searchSymbols: async (q: string): Promise<SymbolSearchResult[]> => {
    return await request<SymbolSearchResult[]>(`/market/search?q=${encodeURIComponent(q)}`);
  },

  getQuote: async (symbol: string): Promise<Quote> => {
    const raw = await request<any>(`/market/quote/${encodeURIComponent(symbol)}`);
    return {
      symbol: raw.symbol,
      company: raw.company || raw.name || raw.symbol,
      name: raw.company || raw.name || raw.symbol,
      current_price: raw.current_price ?? raw.c ?? 100.0,
      previous_close: raw.previous_close ?? raw.pc ?? 100.0,
      change: raw.change ?? raw.d ?? 0.0,
      change_percent: raw.change_percent ?? raw.dp ?? 0.0,
      volume: raw.volume ?? 0,
      high: raw.high ?? raw.h ?? raw.current_price ?? 100.0,
      low: raw.low ?? raw.l ?? raw.current_price ?? 100.0,
      open: raw.open ?? raw.o ?? raw.current_price ?? 100.0,
      timestamp: raw.timestamp ?? raw.t ?? Math.floor(Date.now() / 1000),
      simulated: Boolean(raw.simulated),
      c: raw.current_price ?? raw.c ?? 100.0,
      d: raw.change ?? raw.d ?? 0.0,
      dp: raw.change_percent ?? raw.dp ?? 0.0,
      h: raw.high ?? raw.h ?? raw.current_price ?? 100.0,
      l: raw.low ?? raw.l ?? raw.current_price ?? 100.0,
      o: raw.open ?? raw.o ?? raw.current_price ?? 100.0,
      pc: raw.previous_close ?? raw.pc ?? 100.0,
      t: raw.timestamp ?? raw.t ?? Math.floor(Date.now() / 1000),
    };
  },

  getOHLCV: async (symbol: string, range: string = "1D", count: number = 100): Promise<OHLCVData> => {
    return await request<OHLCVData>(
      `/market/ohlcv/${encodeURIComponent(symbol)}?range=${range}&count=${count}`
    );
  },

  getNews: async (symbol: string): Promise<NewsArticle[]> => {
    return await request<NewsArticle[]>(`/market/news/${encodeURIComponent(symbol)}`);
  },

  // Trading
  submitOrder: async (input: OrderInput): Promise<Trade> => {
    return await request<Trade>("/trading/orders", {
      method: "POST",
      body: JSON.stringify({
        symbol: input.symbol,
        side: input.side,
        quantity: Math.floor(input.quantity),
        order_type: input.order_type || "MARKET",
        price: input.price,
      }),
    });
  },

  buyStock: async (symbol: string, quantity: number, price?: number): Promise<Trade> => {
    return await request<Trade>("/trading/orders", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        side: "BUY",
        quantity: Math.floor(quantity),
        order_type: "MARKET",
        price,
      }),
    });
  },

  sellStock: async (symbol: string, quantity: number, price?: number): Promise<Trade> => {
    return await request<Trade>("/trading/orders", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        side: "SELL",
        quantity: Math.floor(quantity),
        order_type: "MARKET",
        price,
      }),
    });
  },

  getTradeHistory: async (limit: number = 50): Promise<Trade[]> => {
    return await request<Trade[]>(`/trading/orders/history?limit=${limit}`);
  },

  // Portfolio
  getPortfolio: async (): Promise<PortfolioResponse> => {
    return await request<PortfolioResponse>("/portfolio");
  },

  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    return await request<PortfolioSummary>("/portfolio/summary");
  },

  getPositions: async (): Promise<Position[]> => {
    return await request<Position[]>("/portfolio/positions");
  },

  getTransactions: async (limit: number = 50): Promise<Transaction[]> => {
    return await request<Transaction[]>(`/portfolio/transactions?limit=${limit}`);
  },

  // Watchlist
  getWatchlist: async (): Promise<WatchlistItem[]> => {
    return await request<WatchlistItem[]>("/watchlist");
  },

  getWatchlists: async (): Promise<Watchlist[]> => {
    return await request<Watchlist[]>("/watchlists/all");
  },

  createWatchlist: async (): Promise<Watchlist> => {
    return await request<Watchlist>("/watchlists", {
      method: "POST",
    });
  },

  deleteWatchlist: async (watchlistId: number): Promise<{ message: string }> => {
    return await request<{ message: string }>(`/watchlists/${watchlistId}`, {
      method: "DELETE",
    });
  },

  getWatchlistItems: async (watchlistId: number): Promise<WatchlistItem[]> => {
    return await request<WatchlistItem[]>(`/watchlists/${watchlistId}/items`);
  },

  addToWatchlist: async (symbol: string, watchlistId?: number): Promise<WatchlistItem> => {
    const endpoint = watchlistId ? `/watchlists/${watchlistId}/items` : "/watchlist/items";
    return await request<WatchlistItem>(endpoint, {
      method: "POST",
      body: JSON.stringify({ symbol }),
    });
  },

  removeFromWatchlist: async (symbol: string, watchlistId?: number): Promise<{ message: string }> => {
    const endpoint = watchlistId
      ? `/watchlists/${watchlistId}/items/${encodeURIComponent(symbol)}`
      : `/watchlist/items/${encodeURIComponent(symbol)}`;
    return await request<{ message: string }>(endpoint, {
      method: "DELETE",
    });
  },

  // AI Intelligence
  getPrediction: async (symbol: string): Promise<PredictionResponse> => {
    return await request<PredictionResponse>(`/ai/prediction/${encodeURIComponent(symbol)}`);
  },

  getSentiment: async (symbol: string): Promise<SentimentResponse> => {
    return await request<SentimentResponse>(`/ai/sentiment/${encodeURIComponent(symbol)}`);
  },

  getPortfolioRisk: async (): Promise<RiskMetricResponse> => {
    return await request<RiskMetricResponse>("/ai/risk/portfolio");
  },

  getSymbolRisk: async (symbol: string): Promise<RiskMetricResponse> => {
    return await request<RiskMetricResponse>(`/ai/risk/symbol/${encodeURIComponent(symbol)}`);
  },

  getSignals: async (limit: number = 10): Promise<SignalScanItem[]> => {
    return await request<SignalScanItem[]>(`/ai/signals/active?limit=${limit}`);
  },

  // Swarm
  getSwarm: async (symbol: string): Promise<SwarmConsensusResponse> => {
    return await request<SwarmConsensusResponse>(`/swarm/${encodeURIComponent(symbol)}`);
  },

  // Backtester
  runBacktest: async (payload: {
    symbol: string;
    strategy_prompt?: string;
    strategy_type?: string;
    initial_cash?: number;
    bars_count?: number;
    params?: Record<string, number>;
  }): Promise<BacktestResult> => {
    return await request<BacktestResult>("/backtest/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Autopilot
  getAutopilotStatus: async (): Promise<AutopilotStatusResponse> => {
    return await request<AutopilotStatusResponse>("/autopilot/status");
  },

  updateAutopilotConfig: async (config: Partial<AutopilotConfig>): Promise<AutopilotConfig> => {
    return await request<AutopilotConfig>("/autopilot/config", {
      method: "POST",
      body: JSON.stringify(config),
    });
  },

  // Correlation Network
  getCorrelationNetwork: async (): Promise<CorrelationNetworkResponse> => {
    return await request<CorrelationNetworkResponse>("/correlation/network");
  },

  // Command Palette
  parseCommand: async (command: string): Promise<CommandParseResponse> => {
    return await request<CommandParseResponse>("/command/parse", {
      method: "POST",
      body: JSON.stringify({ command }),
    });
  },
};
