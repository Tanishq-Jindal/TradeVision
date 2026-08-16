"use client";

import React, { useEffect, useState } from "react";
import { SignalScanItem } from "@/types";
import { api } from "@/lib/api";
import { Radio, Sparkles, TrendingUp, TrendingDown, ArrowRight, RefreshCw } from "lucide-react";

interface SignalScannerWidgetProps {
  onSelectSymbol: (symbol: string) => void;
}

export const SignalScannerWidget: React.FC<SignalScannerWidgetProps> = ({ onSelectSymbol }) => {
  const [signals, setSignals] = useState<SignalScanItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const data = await api.getSignals(6);
      setSignals(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Autonomous Signal Scanner
          </h3>
        </div>
        <button
          onClick={fetchSignals}
          disabled={loading}
          className="text-slate-400 hover:text-white transition p-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Signals List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {loading && signals.length === 0 ? (
          <div className="col-span-full py-8 text-center text-xs text-slate-500 animate-pulse">
            Scanning market opportunities...
          </div>
        ) : (
          signals.map((sig) => {
            const isBuy = sig.signal_type.includes("BUY");
            const isSell = sig.signal_type.includes("SELL");

            return (
              <div
                key={sig.id}
                onClick={() => onSelectSymbol(sig.symbol)}
                className="p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-sm text-white group-hover:text-blue-400 transition">
                      {sig.symbol}
                    </div>
                    <div className="text-[10px] text-slate-400">{sig.name}</div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        isBuy
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : isSell
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {sig.signal_type.replace("_", " ")}
                    </span>
                    <div className="font-mono text-xs font-bold text-slate-200 mt-1">
                      Score: {sig.composite_score}/100
                    </div>
                  </div>
                </div>

                {/* Key Drivers */}
                <div className="space-y-1 pt-1 border-t border-slate-800/60 text-[11px] text-slate-400">
                  {sig.key_drivers.map((driver, i) => (
                    <div key={i} className="flex items-center gap-1.5 truncate">
                      <div className="w-1 h-1 rounded-full bg-blue-400 shrink-0" />
                      <span className="truncate">{driver}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
