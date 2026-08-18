"use client";

import React, { useState } from "react";
import { BacktestResult } from "@/types";
import { api } from "@/lib/api";
import { formatSymbolDisplay } from "@/lib/utils";
import { Play, TrendingUp, TrendingDown, Clock, ShieldCheck, X, Loader2, Sparkles } from "lucide-react";

interface BacktestModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
}

export const BacktestModal: React.FC<BacktestModalProps> = ({ isOpen, onClose, symbol }) => {
  const [strategyPrompt, setStrategyPrompt] = useState<string>(
    "Buy when RSI is below 35 and sell when RSI is above 65"
  );
  const [strategyType, setStrategyType] = useState<string>("RSI_MOMENTUM");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<BacktestResult | null>(null);

  if (!isOpen) return null;

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await api.runBacktest({
        symbol,
        strategy_prompt: strategyPrompt,
        strategy_type: strategyType,
        initial_cash: 100000.0,
        bars_count: 100,
      });
      setResult(data);
    } catch (e) {
      console.error("Backtest execution error:", e);
    } finally {
      setLoading(false);
    }
  };

  const isProfit = result ? result.total_return >= 0 : true;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-950 border border-slate-800/90 rounded-2xl p-6 shadow-2xl space-y-6 relative">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              Natural Language Strategy Backtester: {formatSymbolDisplay(symbol)}
            </h3>
            <p className="text-xs text-slate-400">
              Simulate quantitative rules over historical daily price bars
            </p>
          </div>
        </div>

        {/* Strategy Input Form */}
        <form onSubmit={handleRun} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Natural Language Strategy Description
            </label>
            <input
              type="text"
              value={strategyPrompt}
              onChange={(e) => setStrategyPrompt(e.target.value)}
              placeholder="e.g. Buy when RSI is below 30 and sell when above 70"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            />
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              onClick={() => {
                setStrategyPrompt("Buy when RSI is below 30 and sell when above 70");
                setStrategyType("RSI_MOMENTUM");
              }}
              className="px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-[11px] font-medium transition"
            >
              RSI Mean Reversion (30/70)
            </button>
            <button
              type="button"
              onClick={() => {
                setStrategyPrompt("Buy when 10-day SMA crosses above 30-day SMA, sell on cross below");
                setStrategyType("SMA_CROSSOVER");
              }}
              className="px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-[11px] font-medium transition"
            >
              SMA Trend Crossover (10/30)
            </button>
            <button
              type="button"
              onClick={() => {
                setStrategyPrompt("Buy when MACD histogram turns positive, sell when negative");
                setStrategyType("MACD_MOMENTUM");
              }}
              className="px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-[11px] font-medium transition"
            >
              MACD Momentum
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-xs text-white shadow-lg shadow-purple-600/25 transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Simulating Strategy...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                Run Backtest Simulation ($100,000 Portfolio)
              </>
            )}
          </button>
        </form>

        {/* Backtest Results */}
        {result && (
          <div className="space-y-4 pt-4 border-t border-slate-800/80">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Performance Attribution: {result.strategy_name}
            </h4>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[10px] uppercase font-semibold">Total Return</div>
                <div
                  className={`font-mono font-bold text-sm ${
                    isProfit ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {isProfit ? "+" : ""}
                  {result.total_return_pct.toFixed(2)}%
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[10px] uppercase font-semibold">Win Rate</div>
                <div className="font-mono font-bold text-sm text-slate-200">
                  {result.win_rate.toFixed(1)}%
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[10px] uppercase font-semibold">Sharpe Ratio</div>
                <div className="font-mono font-bold text-sm text-slate-200">
                  {result.sharpe_ratio.toFixed(2)}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
                <div className="text-slate-400 text-[10px] uppercase font-semibold">Max Drawdown</div>
                <div className="font-mono font-bold text-sm text-rose-400">
                  -{result.max_drawdown.toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Trades Executed */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Simulated Trades ({result.trades.length})</span>
                <span>
                  {result.winning_trades} Wins / {result.losing_trades} Losses
                </span>
              </div>
              <div className="max-h-40 overflow-y-auto rounded-xl border border-slate-800/80 divide-y divide-slate-800/60 text-xs">
                {result.trades.map((t, idx) => {
                  const isTradeWin = t.pnl >= 0;
                  return (
                    <div key={idx} className="p-2.5 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-slate-200">
                          {t.shares} shares @ ${t.entry_price.toFixed(2)} → ${t.exit_price.toFixed(2)}
                        </span>
                      </div>
                      <div
                        className={`font-mono font-bold ${
                          isTradeWin ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {isTradeWin ? "+" : ""}
                        ${t.pnl.toFixed(2)} ({isTradeWin ? "+" : ""}
                        {t.pnl_pct.toFixed(2)}%)
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
