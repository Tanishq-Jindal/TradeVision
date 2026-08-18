"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { MarketMoversResponse, MoverItem } from "@/types";
import { TrendingUp, TrendingDown, RefreshCw, Zap, AlertCircle } from "lucide-react";

interface MarketMoversProps {
  onSelectSymbol?: (symbol: string) => void;
}

export const MarketMovers: React.FC<MarketMoversProps> = ({ onSelectSymbol }) => {
  const [data, setData] = useState<MarketMoversResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMovers = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const res = await api.getMarketMovers(6);
      setData(res);
      setError(null);
    } catch (err: any) {
      console.warn("Failed to fetch market movers:", err);
      if (!data) {
        setError("Market data unavailable");
      }
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMovers();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => fetchMovers(), 30000);
    return () => clearInterval(interval);
  }, []);

  const renderMoverList = (items: MoverItem[], isGainer: boolean) => {
    if (loading && !data) {
      return (
        <div className="space-y-2.5">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-10 rounded-xl bg-slate-900/60 border border-slate-800/40 animate-pulse"
            />
          ))}
        </div>
      );
    }

    if (items.length === 0) {
      return (
        <div className="text-center py-4 text-xs text-slate-500">
          No mover data available
        </div>
      );
    }

    return (
      <div className="space-y-1.5">
        {items.map((item) => {
          const isPositive = item.change_percent >= 0;
          return (
            <div
              key={item.symbol}
              onClick={() => onSelectSymbol?.(item.symbol)}
              className="group flex items-center justify-between p-2.5 rounded-xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800/50 hover:border-slate-700/80 transition-all duration-150 cursor-pointer"
            >
              {/* Left: Rank & Ticker */}
              <div className="flex items-center gap-2.5 min-w-0 pr-2">
                <span
                  className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold shrink-0 ${
                    isGainer
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {item.rank}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-xs text-white group-hover:text-blue-400 transition-colors">
                      {item.symbol}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 truncate max-w-[120px] sm:max-w-[150px]">
                    {item.company}
                  </p>
                </div>
              </div>

              {/* Right: Price & % Change */}
              <div className="text-right shrink-0">
                <div className="text-xs font-mono font-semibold text-slate-200">
                  ${item.price.toFixed(2)}
                </div>
                <div
                  className={`text-[11px] font-mono font-bold flex items-center justify-end gap-0.5 ${
                    isPositive ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {item.change_percent.toFixed(2)}%
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* 1. Header Section */}
      <div className="rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900/90 to-blue-950/20 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl">
        <div className="flex items-center justify-between mb-1.5">
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
            <Zap className="w-3 h-3 text-emerald-400 fill-emerald-400" />
            Market Movers
          </div>
          <button
            onClick={() => fetchMovers(true)}
            disabled={loading || refreshing}
            title="Refresh market movers"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-blue-400" : ""}`} />
          </button>
        </div>
        <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">
          What&apos;s moving. Right now.
        </h2>
        <p className="text-[11px] text-slate-400 mt-0.5">
          Real-time top gainers &amp; losers across global US equity markets.
        </p>
      </div>

      {error ? (
        <div className="rounded-2xl bg-slate-950/80 border border-rose-500/20 p-4 text-center space-y-2">
          <AlertCircle className="w-5 h-5 text-rose-400 mx-auto" />
          <p className="text-xs text-rose-300 font-medium">{error}</p>
          <button
            onClick={() => fetchMovers(true)}
            className="px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg transition"
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          {/* 2. Top Gainers Card */}
          <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-4 backdrop-blur-xl shadow-xl space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                    Top Gainers
                  </h3>
                  <span className="text-[10px] text-slate-400">Leading momentum</span>
                </div>
              </div>
              <span className="text-[10px] font-semibold text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                Top 6
              </span>
            </div>

            {renderMoverList(data?.gainers || [], true)}
          </div>

          {/* 3. Top Losers Card */}
          <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-4 backdrop-blur-xl shadow-xl space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                  <TrendingDown className="w-4 h-4 text-rose-400" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                    Top Losers
                  </h3>
                  <span className="text-[10px] text-slate-400">Downside pullbacks</span>
                </div>
              </div>
              <span className="text-[10px] font-semibold text-rose-400 px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/20">
                Top 6
              </span>
            </div>

            {renderMoverList(data?.losers || [], false)}
          </div>

          {/* 4. Footer info */}
          <div className="px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800/50 flex items-center justify-between text-[10px] text-slate-400">
            <span>
              {data?.market_status === "Closed"
                ? "Prices from latest market session"
                : "Prices are real-time"}
            </span>
            <span className="text-slate-400 font-medium">
              Source: {data?.source || "Market Data Feed"}
            </span>
          </div>
        </>
      )}
    </div>
  );
};
