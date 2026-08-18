"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  TrendingUp,
  ShieldCheck,
  Zap,
  Terminal,
  ExternalLink,
  DollarSign,
  User as UserIcon,
  LogOut,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Wallet,
  RefreshCw,
  Sliders,
  Play,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import {
  HealthResponse,
  Quote,
  CandleBar,
  Position,
  Trade,
  PortfolioSummary,
  WatchlistItem,
  SwarmConsensusResponse,
} from "@/types";
import { HealthBadge } from "@/components/HealthBadge";
import { useAuth } from "@/context/AuthContext";
import { PriceChart } from "@/components/PriceChart";
import { OrderModal } from "@/components/OrderModal";
import { PositionsTable } from "@/components/PositionsTable";
import { WatchlistWidget } from "@/components/WatchlistWidget";
import { RecentTrades } from "@/components/RecentTrades";
import { PortfolioHeader } from "@/components/PortfolioHeader";
import { SwarmConsensusWidget } from "@/components/SwarmConsensusWidget";
import { SignalScannerWidget } from "@/components/SignalScannerWidget";
import { AIAdvisorWidget } from "@/components/AIAdvisorWidget";
import { BacktestModal } from "@/components/BacktestModal";
import { CommandPalette } from "@/components/CommandPalette";
import { AutopilotWidget } from "@/components/AutopilotWidget";
import { CorrelationWidget } from "@/components/CorrelationWidget";
import { MarketMovers } from "@/components/MarketMovers";
import { GlobalMarketPulse } from "@/components/GlobalMarketPulse";
import { formatSymbolDisplay } from "@/lib/utils";

export default function HomePage() {
  const { user, loading: authLoading, logout, login } = useAuth();

  // Selected Stock & Market State
  const [selectedSymbol, setSelectedSymbol] = useState<string>("NVDA");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [candles, setCandles] = useState<CandleBar[]>([]);
  const [loadingChart, setLoadingChart] = useState<boolean>(true);

  // Swarm State
  const [swarm, setSwarm] = useState<SwarmConsensusResponse | null>(null);
  const [loadingSwarm, setLoadingSwarm] = useState<boolean>(true);

  // User Trading & Portfolio State
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);

  // Modals & Overlay
  const [isOrderModalOpen, setIsOrderModalOpen] = useState<boolean>(false);
  const [isBacktestModalOpen, setIsBacktestModalOpen] = useState<boolean>(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);

  // Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [loggingInDemo, setLoggingInDemo] = useState<boolean>(false);

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const fetchSymbolData = async (sym: string) => {
    setLoadingChart(true);
    setLoadingSwarm(true);
    try {
      const [q, ohlcv, sw] = await Promise.all([
        api.getQuote(sym),
        api.getOHLCV(sym, "1D", 80),
        api.getSwarm(sym),
      ]);
      setQuote(q);
      setCandles(ohlcv.candles);
      setSwarm(sw);
    } catch (e) {
      console.error("Symbol data error:", e);
    } finally {
      setLoadingChart(false);
      setLoadingSwarm(false);
    }
  };

  const fetchUserData = async () => {
    if (!user) return;
    try {
      const [summary, pos, trds, wl] = await Promise.all([
        api.getPortfolioSummary(),
        api.getPositions(),
        api.getTradeHistory(15),
        api.getWatchlist(),
      ]);
      setPortfolioSummary(summary);
      setPositions(pos);
      setTrades(trds);
      setWatchlist(wl);
    } catch (e) {
      console.error("User data error:", e);
    }
  };

  const fetchHealth = async () => {
    setLoadingHealth(true);
    setHealthError(null);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setHealthError(`[${err.code}] ${err.message}`);
      } else {
        setHealthError("Backend offline");
      }
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  useEffect(() => {
    fetchSymbolData(selectedSymbol);
  }, [selectedSymbol]);

  useEffect(() => {
    if (user) {
      fetchUserData();
      const interval = setInterval(fetchUserData, 10000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleQuickDemoLogin = async () => {
    setLoggingInDemo(true);
    try {
      await login({ email: "demo@tradevision.cloud", password: "demo123" });
    } catch (err) {
      console.error("Demo login error:", err);
    } finally {
      setLoggingInDemo(false);
    }
  };

  const currentHeldPosition = positions.find((p) => p.symbol === selectedSymbol);

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col justify-between">
      {/* Ambient background lighting */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[450px] bg-blue-600/10 blur-[150px] rounded-full" />
        <div className="absolute top-1/3 left-1/4 w-[600px] h-[400px] bg-emerald-600/5 blur-[140px] rounded-full" />
      </div>

      {/* Header */}
      <header className="relative z-20 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                TradeVision
              </span>
              <span className="ml-2.5 text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                AI Trading Intelligence
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Command Palette Trigger */}
            <button
              onClick={() => setIsCommandPaletteOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs text-slate-300 transition"
            >
              <Terminal className="w-3.5 h-3.5 text-blue-400" />
              <span>Command Palette</span>
              <kbd className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-slate-400">
                Ctrl+K
              </kbd>
            </button>

            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/50 hover:border-slate-700"
            >
              API Docs
              <ExternalLink className="w-3 h-3 text-slate-500" />
            </a>

            {authLoading ? (
              <div className="w-24 h-8 rounded-lg bg-slate-900 animate-pulse" />
            ) : user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="font-medium text-slate-200">{user.display_name || user.email}</span>
                </div>
                <button
                  onClick={() => logout()}
                  className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-rose-400 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-rose-500/30 px-3 py-1.5 rounded-lg transition"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-xs font-medium text-slate-300 hover:text-white px-3.5 py-1.5 rounded-lg hover:bg-slate-800 transition"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 px-3.5 py-1.5 rounded-lg shadow-sm shadow-blue-600/30 transition"
                >
                  Get $100k Cash
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Terminal Body */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8 w-full space-y-6">
        {user ? (
          <>
            {/* Portfolio Summary Header */}
            <PortfolioHeader
              summary={portfolioSummary}
              onTradeClick={() => setIsOrderModalOpen(true)}
            />

            {/* Autonomous Signal Scanner */}
            <SignalScannerWidget onSelectSymbol={(sym) => setSelectedSymbol(sym)} />

            {/* Primary Workspace Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left 2 Columns: Charts & Analytics */}
              <div className="lg:col-span-2 space-y-6">
                <PriceChart
                  symbol={selectedSymbol}
                  quote={quote}
                  candles={candles}
                  isLoading={loadingChart}
                />

                {/* Multi-Agent Swarm Deliberation */}
                <SwarmConsensusWidget swarm={swarm} isLoading={loadingSwarm} />

                {/* Open Positions Table */}
                <PositionsTable
                  positions={positions}
                  onSelectPosition={(sym) => setSelectedSymbol(sym)}
                  onTradeAction={(sym) => {
                    setSelectedSymbol(sym);
                    setIsOrderModalOpen(true);
                  }}
                />

                {/* Autopilot Guardrails & Actions */}
                <AutopilotWidget />

                {/* Cross-Asset Correlation Network */}
                <CorrelationWidget />

                {/* Recent Trade History */}
                <RecentTrades trades={trades} />
              </div>

              {/* Right Column: Watchlist & AI Advisor */}
              <div className="space-y-6">
                {/* Watchlist */}
                <WatchlistWidget
                  items={watchlist}
                  selectedSymbol={selectedSymbol}
                  onSelectSymbol={(sym) => setSelectedSymbol(sym)}
                  onWatchlistChanged={fetchUserData}
                />

                {/* Quick Action Tools */}
                <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800/80 backdrop-blur-xl shadow-xl space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Fast Execution Tools
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setIsOrderModalOpen(true)}
                      className="py-2.5 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 font-bold text-xs text-white transition flex items-center justify-center gap-1.5"
                    >
                      <DollarSign className="w-3.5 h-3.5" />
                      Trade {formatSymbolDisplay(selectedSymbol)}
                    </button>
                    <button
                      onClick={() => setIsBacktestModalOpen(true)}
                      className="py-2.5 px-3 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-xs text-white transition flex items-center justify-center gap-1.5"
                    >
                      <Play className="w-3.5 h-3.5 fill-white" />
                      Backtest Strategy
                    </button>
                  </div>
                </div>

                {/* Conversational AI Financial Advisor */}
                <AIAdvisorWidget symbol={selectedSymbol} />

                {/* Global Market Pulse Indices Card */}
                <GlobalMarketPulse onSelectSymbol={(sym) => setSelectedSymbol(sym)} />

                {/* Real-Time Market Movers Sidebar */}
                <MarketMovers onSelectSymbol={(sym) => setSelectedSymbol(sym)} />
              </div>
            </div>
          </>
        ) : (
          /* Unauthenticated Landing */
          <div className="p-10 rounded-2xl bg-gradient-to-br from-slate-950/90 via-slate-900/70 to-blue-950/20 border border-slate-800/80 backdrop-blur-xl shadow-2xl space-y-6 text-center max-w-3xl mx-auto my-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              Full AI Paper Trading & Portfolio Intelligence Platform Ready
            </div>
            <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-white leading-tight">
              Master Equities Trading With Layered AI Intelligence
            </h1>
            <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">
              Experience the full TradeVision terminal: ML directional signals, 4-agent swarm consensus, autonomous signal scanning, natural language backtesting, and guardrailed autopilot paper execution.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <Link
                href="/register"
                className="py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 font-bold text-sm text-white shadow-lg shadow-blue-600/30 transition flex items-center gap-2"
              >
                Create Account ($100k Virtual Cash)
                <ArrowRight className="w-4 h-4" />
              </Link>
              <button
                onClick={handleQuickDemoLogin}
                disabled={loggingInDemo}
                className="py-3 px-5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 font-bold text-sm text-slate-200 transition flex items-center gap-2 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4 text-blue-400" />
                {loggingInDemo ? "Signing in..." : "Instant Demo Login"}
              </button>
            </div>
          </div>
        )}

        {/* System Diagnostics Footer Card */}
        <div className="p-6 rounded-2xl bg-slate-950/70 border border-slate-800/80 backdrop-blur-xl shadow-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                System Infrastructure Status
              </h3>
            </div>
            <button
              onClick={fetchHealth}
              disabled={loadingHealth}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
            >
              <RefreshCw className={`w-3 h-3 ${loadingHealth ? "animate-spin" : ""}`} />
              Refresh Probes
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <HealthBadge
              name="PostgreSQL Database"
              service={health?.services?.database}
              isLoading={loadingHealth && !health}
            />
            <HealthBadge
              name="Redis Cache & Queue"
              service={health?.services?.redis}
              isLoading={loadingHealth && !health}
            />
          </div>
        </div>
      </main>

      {/* Order Placement Modal */}
      {user && (
        <OrderModal
          isOpen={isOrderModalOpen}
          onClose={() => setIsOrderModalOpen(false)}
          symbol={selectedSymbol}
          quote={quote}
          cashBalance={portfolioSummary?.cash_balance ?? 100000.00}
          existingPosition={currentHeldPosition}
          onTradeSuccess={() => {
            fetchUserData();
            fetchSymbolData(selectedSymbol);
          }}
        />
      )}

      {/* Backtest Strategy Modal */}
      <BacktestModal
        isOpen={isBacktestModalOpen}
        onClose={() => setIsBacktestModalOpen(false)}
        symbol={selectedSymbol}
      />

      {/* Natural Language Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectSymbol={(sym) => setSelectedSymbol(sym)}
        onTriggerTrade={(sym) => {
          setSelectedSymbol(sym);
          setIsOrderModalOpen(true);
        }}
        onTriggerBacktest={(sym) => {
          setSelectedSymbol(sym);
          setIsBacktestModalOpen(true);
        }}
        onRefreshData={() => {
          fetchUserData();
          fetchSymbolData(selectedSymbol);
        }}
      />

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/80 bg-slate-950/40 px-6 py-6 text-center text-xs text-slate-500">
        TradeVision · Full-Stack AI Paper Trading & Portfolio Intelligence Platform · Real-Time Markets. Smarter Decisions.
      </footer>
    </div>
  );
}
