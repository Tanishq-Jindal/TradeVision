"use client";

import React from "react";
import { Trade } from "@/types";
import { History, ArrowDownLeft, ArrowUpRight } from "lucide-react";

interface RecentTradesProps {
  trades: Trade[];
}

export const RecentTrades: React.FC<RecentTradesProps> = ({ trades }) => {
  if (trades.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Trade Execution Log
          </h3>
        </div>
        <span className="text-xs text-slate-500">{trades.length} Executed</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/50 text-slate-400 font-medium uppercase text-[10px] tracking-wider border-b border-slate-800/60">
            <tr>
              <th className="py-2.5 px-3">Side</th>
              <th className="py-2.5 px-3">Symbol</th>
              <th className="py-2.5 px-3">Shares</th>
              <th className="py-2.5 px-3">Execution Price</th>
              <th className="py-2.5 px-3">Total Value</th>
              <th className="py-2.5 px-3 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {trades.slice(0, 10).map((t) => {
              const isBuy = t.side === "BUY";
              return (
                <tr key={t.id} className="hover:bg-slate-900/40 transition">
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isBuy
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {isBuy ? <ArrowDownLeft className="w-3 h-3" /> : <ArrowUpRight className="w-3 h-3" />}
                      {t.side}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-bold text-white">{t.symbol}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-300">
                    {t.quantity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-300">${t.price.toFixed(2)}</td>
                  <td className="py-2.5 px-3 font-mono font-semibold text-slate-100">
                    ${t.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-500 text-right">
                    {new Date(t.executed_at).toLocaleTimeString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
