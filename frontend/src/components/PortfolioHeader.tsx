"use client";

import React from "react";
import { PortfolioSummary } from "@/types";
import { Wallet, DollarSign, TrendingUp, TrendingDown, PieChart, Layers } from "lucide-react";

interface PortfolioHeaderProps {
  summary?: PortfolioSummary | null;
  onTradeClick: () => void;
}

export const PortfolioHeader: React.FC<PortfolioHeaderProps> = ({ summary, onTradeClick }) => {
  const totalVal = summary?.total_value ?? 100000.00;
  const cashBal = summary?.cash_balance ?? 100000.00;
  const investedVal = summary?.invested_value ?? 0.00;
  const totalPnl = summary?.total_pnl ?? 0.00;
  const totalPnlPct = summary?.total_pnl_pct ?? 0.00;
  const dailyPnl = summary?.daily_pnl ?? 0.00;
  const dailyPnlPct = summary?.daily_pnl_pct ?? 0.00;

  const isTotalProfit = totalPnl >= 0;
  const isDailyProfit = dailyPnl >= 0;

  return (
    <div className="rounded-2xl bg-gradient-to-br from-slate-950/90 via-slate-900/80 to-blue-950/20 border border-slate-800/90 p-6 backdrop-blur-xl shadow-2xl space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-800/80">
        <div className="space-y-1">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Wallet className="w-3.5 h-3.5 text-blue-400" />
            Total Portfolio Value
          </div>
          <div className="text-4xl font-black text-white font-mono tracking-tight">
            ${totalVal.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6">
          <div className="space-y-1">
            <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Today&apos;s Return
            </div>
            <div
              className={`flex items-center gap-1 text-lg font-bold font-mono ${
                isDailyProfit ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {isDailyProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>
                {isDailyProfit ? "+" : ""}
                ${dailyPnl.toFixed(2)} ({isDailyProfit ? "+" : ""}
                {dailyPnlPct.toFixed(2)}%)
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Total Paper Return
            </div>
            <div
              className={`flex items-center gap-1 text-lg font-bold font-mono ${
                isTotalProfit ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {isTotalProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>
                {isTotalProfit ? "+" : ""}
                ${totalPnl.toFixed(2)} ({isTotalProfit ? "+" : ""}
                {totalPnlPct.toFixed(2)}%)
              </span>
            </div>
          </div>

          <button
            onClick={onTradeClick}
            className="py-2.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 font-bold text-sm text-white shadow-lg shadow-blue-600/30 transition flex items-center gap-2"
          >
            <DollarSign className="w-4 h-4" />
            Trade Now
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <div className="text-slate-400 uppercase tracking-wider text-[10px] font-medium">
            Available Virtual Cash
          </div>
          <div className="text-emerald-400 font-mono font-bold text-base">
            ${cashBal.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <div className="text-slate-400 uppercase tracking-wider text-[10px] font-medium">
            Invested Equity Value
          </div>
          <div className="text-slate-200 font-mono font-bold text-base">
            ${investedVal.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <div className="text-slate-400 uppercase tracking-wider text-[10px] font-medium">
            Active Holdings
          </div>
          <div className="text-slate-200 font-mono font-bold text-base">
            {summary?.positions_count || 0} Open Positions
          </div>
        </div>
      </div>
    </div>
  );
};
