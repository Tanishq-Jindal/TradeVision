export interface ServiceHealth {
  status: "ok" | "unhealthy" | "disabled" | "not_configured" | string;
  latency_ms?: number;
  error?: string | null;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "unhealthy";
  db: string;
  redis: string;
  version: string;
  timestamp: string;
  services: {
    database: ServiceHealth;
    redis: ServiceHealth;
  };
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

export interface Portfolio {
  id: number;
  user_id: number;
  cash_balance: number;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  display_name: string | null;
  created_at: string;
  portfolio?: Portfolio | null;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  display_name?: string;
}

export interface Quote {
  symbol: string;
  company?: string;
  name?: string;
  current_price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  timestamp?: number;
  simulated?: boolean;
  provider?: string;
  market_status?: string;
  source?: string;
  c: number;
  d: number;
  dp: number;
  h: number;
  l: number;
  o: number;
  pc: number;
  t: number;
}

export interface SymbolSearchResult {
  symbol: string;
  description: string;
  type: string;
  currency: string;
  sector?: string | null;
}

export interface CandleBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OHLCVData {
  symbol: string;
  timeframe: string;
  candles: CandleBar[];
  simulated: boolean;
}

export interface NewsArticle {
  id: string;
  headline: string;
  summary: string;
  source: string;
  url: string;
  datetime: number;
  symbol: string;
}

export interface MoverItem {
  rank: number;
  symbol: string;
  company: string;
  price: number;
  change: number;
  change_percent: number;
  market_status?: string;
}

export interface MarketMoversResponse {
  gainers: MoverItem[];
  losers: MoverItem[];
  updated_at: number;
  market_status: string;
  source: string;
  simulated: boolean;
}

export interface MarketIndexItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  market_status: string;
  etf_proxy?: string | null;
}

export interface MarketPulseResponse {
  indices: MarketIndexItem[];
  updated_at: number;
  market_status: string;
  source: string;
  simulated: boolean;
}

export interface OrderInput {
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  order_type?: "MARKET";
  price?: number;
}

export interface Trade {
  id: number;
  portfolio_id: number;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  total_value: number;
  executed_at: string;
}

export interface PositionDetail {
  id?: number;
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  avg_entry_price?: number;
  unrealized_pnl_pct?: number;
  daily_change_pct?: number;
  updated_at?: string;
}

export interface Position {
  id: number;
  symbol: string;
  quantity: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  daily_change_pct: number;
  updated_at: string;
}

export interface Transaction {
  id: number;
  type: string;
  amount: number;
  balance_after: number;
  related_trade_id?: number | null;
  created_at: string;
}

export interface PortfolioResponse {
  cash_balance: number;
  total_market_value: number;
  total_portfolio_value: number;
  invested_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  positions: PositionDetail[];
}

export interface PortfolioSummary {
  cash_balance: number;
  invested_value: number;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  positions_count: number;
}

export interface WatchlistItem {
  id: number;
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  added_at: string;
}

export interface Watchlist {
  id: number;
  user_id: number;
  created_at: string;
  items: WatchlistItem[];
}

export interface PredictionResponse {
  symbol: string;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  probability: number;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  horizon: string;
  features_importance: Record<string, number>;
  model_version: string;
  timestamp: number;
}

export interface SentimentResponse {
  symbol: string;
  overall_score: number;
  sentiment_label: string;
  bullish_pct: number;
  bearish_pct: number;
  neutral_pct: number;
  articles: Array<{
    id: string;
    headline: string;
    summary: string;
    source: string;
    score: number;
    label: string;
    url: string;
    datetime: number;
  }>;
  summary_insight: string;
  timestamp: number;
}

export interface RiskMetricResponse {
  symbol_or_portfolio: string;
  annualized_volatility: number;
  var_95: number;
  cvar_95: number;
  max_drawdown: number;
  sharpe_ratio: number;
  monte_carlo_simulations: number;
  value_at_risk_interpretation?: string;
  suggested_action?: string;
  stress_test_scenario?: {
    recession_shock_loss_pct: number;
    interest_rate_spike_loss_pct: number;
    tech_bubble_burst_loss_pct: number;
  };
}

export interface SignalScanItem {
  id: string;
  symbol: string;
  name: string;
  company_name: string;
  price: number;
  change_pct: number;
  signal_type: string;
  timeframe: string;
  ai_summary: string;
  confidence_score: number;
  composite_score: number;
  key_drivers: string[];
}

export interface SwarmAgentVote {
  name: string;
  agent_name?: string;
  role: string;
  signal: string;
  bias: string;
  stance: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence: number;
  recommended_weight: number;
  target_price: number;
  reasoning: string;
}

export interface SwarmConsensusResponse {
  symbol: string;
  consensus_action: string;
  consensus_signal: string;
  consensus_score: number;
  agreement_percentage: number;
  overall_confidence: number;
  majority_vote_pct: number;
  summary: string;
  deliberation_summary: string;
  agents: SwarmAgentVote[];
  votes: SwarmAgentVote[];
  synthesized_at: string;
}

export interface BacktestTrade {
  id: string;
  entry_time: number;
  exit_time: number;
  type: "BUY" | "SELL";
  entry_price: number;
  exit_price: number;
  shares: number;
  pnl: number;
  pnl_pct: number;
  return_pct: number;
  profit_loss: number;
}

export interface BacktestResult {
  symbol: string;
  strategy_name: string;
  parameters?: Record<string, any>;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  win_rate_pct: number;
  total_return: number;
  total_return_pct: number;
  cumulative_return_pct: number;
  benchmark_return_pct: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  trades: BacktestTrade[];
  trades_log: BacktestTrade[];
}

export interface CommandParseResponse {
  action: string;
  symbol?: string;
  quantity?: number;
  order_type?: string;
  strategy_prompt?: string;
  confidence: number;
  raw_command?: string;
  preview_message?: string;
}

export interface AutopilotConfig {
  user_id?: number;
  enabled: boolean;
  is_enabled?: boolean;
  max_trade_allocation_pct: number;
  max_allocation_per_trade_pct?: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  min_confidence_threshold: number;
  max_daily_drawdown_stop_pct?: number;
  risk_tolerance?: "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE";
  allowed_symbols?: string[];
  updated_at?: string;
}

export interface AutopilotAction {
  id: string;
  action: string;
  action_type: string;
  symbol: string;
  shares: number;
  quantity: number;
  price: number;
  reason: string;
  timestamp: string;
}

export interface AutopilotStatusResponse {
  active: boolean;
  config: AutopilotConfig;
  active_signals_evaluated: number;
  recent_auto_trades: Trade[];
  recent_actions: AutopilotAction[];
  safety_status: string;
}

export interface CorrelationNode {
  id: string;
  symbol: string;
  name: string;
  sector: string;
}

export interface CorrelationEdge {
  source: string;
  target: string;
  correlation: number;
}

export interface CorrelationNetworkResponse {
  nodes: CorrelationNode[];
  edges: CorrelationEdge[];
  links: CorrelationEdge[];
  timestamp: string;
}
