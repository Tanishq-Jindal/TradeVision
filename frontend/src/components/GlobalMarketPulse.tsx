"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { MarketIndexItem, MarketPulseResponse } from "@/types";
import { Globe, AlertCircle, RefreshCw } from "lucide-react";

interface GlobalMarketPulseProps {
  onSelectSymbol?: (symbol: string) => void;
}

export const GlobalMarketPulse: React.FC<GlobalMarketPulseProps> = ({ onSelectSymbol }) => {
  const [data, setData] = useState<MarketPulseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPulse = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const res = await api.getMarketPulse();
      setData(res);
      setError(null);
    } catch (err: any) {
      console.warn("Failed to fetch market pulse:", err);
      if (!data) {
        setError("Market data unavailable");
      }
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPulse();
    const interval = setInterval(() => fetchPulse(), 30000);
    return () => clearInterval(interval);
  }, []);

  const isLive = data?.market_status === "Live";

  const handleIndexClick = (item: MarketIndexItem) => {
    const symbolMap: Record<string, string> = {
      "^GSPC": "SPY",
      "S&P 500": "SPY",
      "^IXIC": "QQQ",
      "NASDAQ": "QQQ",
      "^DJI": "DIA",
      "DOW JONES": "DIA",
      "^VIX": "^VIX",
      "VIX": "^VIX",
    };

    const target = symbolMap[item.symbol] || symbolMap[item.name] || item.etf_proxy || item.symbol;
    if (onSelectSymbol && target) {
      onSelectSymbol(target);
      setTimeout(() => {
        const chartElement = document.getElementById("main-market-chart");
        if (chartElement) {
          chartElement.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 50);
    }
  };

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-4 backdrop-blur-xl shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Globe className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Global Market Pulse
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchPulse(true)}
            disabled={loading || refreshing}
            title="Refresh market pulse"
            className="p-1 rounded-md text-slate-500 hover:text-slate-200 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${refreshing ? "animate-spin text-blue-400" : ""}`} />
          </button>
          {(() => {
            const status = data?.market_status || "Closed";
            if (status === "Live") {
              return (
                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  LIVE
                </div>
              );
            } else if (status === "Pre-Market") {
              return (
                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  PRE-MARKET
                </div>
              );
            } else if (status === "After-Hours") {
              return (
                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  AFTER-HOURS
                </div>
              );
            } else {
              return (
                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-800/80 text-slate-400 border border-slate-700/60">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  MARKET CLOSED
                </div>
              );
            }
          })()}
        </div>
      </div>

      {/* Content */}
      {loading && !data ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-9 rounded-xl bg-slate-900/60 border border-slate-800/40 animate-pulse"
            />
          ))}
        </div>
      ) : error ? (
        <div className="py-3 text-center space-y-1.5">
          <AlertCircle className="w-4 h-4 text-rose-400 mx-auto" />
          <p className="text-[11px] text-rose-300 font-medium">{error}</p>
          <button
            onClick={() => fetchPulse(true)}
            className="px-2.5 py-0.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[10px] text-slate-200 rounded-lg transition"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="space-y-1.5">
          {data?.indices.map((idx) => {
            const isPositive = idx.change_percent >= 0;
            return (
              <div
                key={idx.symbol}
                onClick={() => handleIndexClick(idx)}
                className="group flex items-center justify-between p-2.5 rounded-xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800/50 hover:border-slate-700/80 transition cursor-pointer"
              >
                <div>
                  <div className="font-bold text-xs text-white group-hover:text-blue-400 transition-colors">
                    {idx.name}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs font-mono font-semibold text-slate-200">
                    {idx.price.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>
                  <div
                    className={`text-[10px] font-mono font-bold flex items-center justify-end gap-0.5 ${
                      isPositive ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isPositive ? "+" : ""}
                    {idx.change_percent.toFixed(2)}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div className="pt-2 border-t border-slate-800/50 flex items-center justify-between text-[9px] text-slate-400">
        <span>Real Market Data Feed</span>
        <span>{data ? new Date(data.updated_at * 1000).toLocaleTimeString() : ""}</span>
      </div>
    </div>
  );
};
