"use client";

import React, { useState, useEffect } from "react";
import { CommandParseResponse } from "@/types";
import { api } from "@/lib/api";
import { formatSymbolDisplay } from "@/lib/utils";
import { Terminal, ArrowRight, Loader2, DollarSign, Bookmark, Play, X, Sparkles } from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSymbol: (symbol: string) => void;
  onTriggerTrade: (symbol: string) => void;
  onTriggerBacktest: (symbol: string) => void;
  onRefreshData: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectSymbol,
  onTriggerTrade,
  onTriggerBacktest,
  onRefreshData,
}) => {
  const [command, setCommand] = useState("");
  const [parsed, setParsed] = useState<CommandParseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    if (!command.trim()) {
      setParsed(null);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.parseCommand(command);
        setParsed(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [command]);

  if (!isOpen) return null;

  const handleExecute = async () => {
    if (!parsed || !parsed.symbol) return;
    setExecuting(true);
    try {
      if (parsed.action === "TRADE_BUY" && parsed.quantity) {
        await api.buyStock(parsed.symbol, parsed.quantity);
        onRefreshData();
        onClose();
      } else if (parsed.action === "TRADE_SELL" && parsed.quantity) {
        await api.sellStock(parsed.symbol, parsed.quantity);
        onRefreshData();
        onClose();
      } else if (parsed.action === "ADD_WATCHLIST") {
        await api.addToWatchlist(parsed.symbol);
        onRefreshData();
        onClose();
      } else if (parsed.action === "RUN_BACKTEST") {
        onTriggerBacktest(parsed.symbol);
        onClose();
      } else if (parsed.action === "NAVIGATE_SYMBOL") {
        onSelectSymbol(parsed.symbol);
        onClose();
      }
    } catch (e) {
      console.error("Command execution error:", e);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-slate-950 border border-slate-800/90 rounded-2xl shadow-2xl overflow-hidden space-y-3 p-4">
        {/* Search Input Bar */}
        <div className="relative flex items-center">
          <Terminal className="w-4 h-4 text-blue-400 absolute left-3 pointer-events-none" />
          <input
            type="text"
            autoFocus
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Type a natural language command (e.g. 'Buy 20 NVDA', 'Backtest TSLA')..."
            className="w-full pl-9 pr-8 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono"
          />
          {loading && <Loader2 className="w-4 h-4 text-slate-400 animate-spin absolute right-3" />}
        </div>

        {/* Parsed Intent Card */}
        {parsed && parsed.action !== "UNKNOWN" && (
          <div className="p-3.5 rounded-xl bg-blue-600/10 border border-blue-500/30 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-blue-300 uppercase text-[10px] tracking-wider">
                Recognized Intent: {parsed.action}
              </span>
              {parsed.symbol && (
                <span className="font-bold text-white px-2 py-0.5 rounded bg-blue-500/20">
                  {formatSymbolDisplay(parsed.symbol)}
                </span>
              )}
            </div>
            <p className="text-slate-200">{parsed.preview_message}</p>

            <button
              onClick={handleExecute}
              disabled={executing}
              className="w-full mt-2 py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 font-bold text-white transition flex items-center justify-center gap-2"
            >
              {executing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  Execute Action
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        )}

        {/* Shortcut Quick Hints */}
        <div className="flex items-center justify-between text-[11px] text-slate-500 px-1 pt-1">
          <span>Press ESC to close</span>
          <span>Tip: 'Buy 10 AAPL' or 'Watch META'</span>
        </div>
      </div>
    </div>
  );
};
