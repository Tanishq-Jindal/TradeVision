"use client";

import React from "react";
import { Position } from "@/types";
import { formatSymbolDisplay } from "@/lib/utils";
import { TrendingUp, TrendingDown, ArrowRightLeft, Layers } from "lucide-react";

interface PositionsTableProps {
  positions: Position[];
  onSelectPosition: (symbol: string) => void;
  onTradeAction: (symbol: string) => void;
}

export const PositionsTable: React.FC<PositionsTableProps> = ({
  positions,
  onSelectPosition,
  onTradeAction,
}) => {
  if (positions.length === 0) {
    return (
      <div className="p-8 rounded-2xl bg-slate-950/70 border border-slate-800/80 text-center space-y-2">
        <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
          <Layers className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-200">No Open Positions</h4>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          You currently hold 0 shares. Select a symbol from your watchlist or search to execute your first paper trade.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 overflow-hidden shadow-xl">
      <div className="p-4 border-b border-slate-800/60 flex items-center justify-between">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">
          Open Positions ({positions.length})
        </h3>
        <span className="text-xs text-slate-400">Mark-to-Market Real-Time</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/50 text-slate-400 font-medium uppercase text-[10px] tracking-wider border-b border-slate-800/60">
            <tr>
              <th className="py-3 px-4">Symbol</th>
              <th className="py-3 px-4">Shares</th>
              <th className="py-3 px-4">Avg Entry</th>
              <th className="py-3 px-4">Market Price</th>
              <th className="py-3 px-4">Market Value</th>
              <th className="py-3 px-4">Unrealized P&L</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {positions.map((pos) => {
              const isProfit = pos.unrealized_pnl >= 0;
              return (
                <tr
                  key={pos.id}
                  onClick={() => onSelectPosition(pos.symbol)}
                  className="hover:bg-slate-900/50 transition cursor-pointer group"
                >
                  <td className="py-3.5 px-4 font-bold text-white group-hover:text-blue-400 transition">
                    {formatSymbolDisplay(pos.symbol)}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">
                    {pos.quantity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-400">
                    ${pos.avg_entry_price.toFixed(2)}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-200">
                    ${pos.current_price.toFixed(2)}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-200">
                    ${pos.market_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold">
                    <div
                      className={`flex items-center gap-1 ${
                        isProfit ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {isProfit ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                      <span>
                        {isProfit ? "+" : ""}
                        ${pos.unrealized_pnl.toFixed(2)} ({isProfit ? "+" : ""}
                        {pos.unrealized_pnl_pct.toFixed(2)}%)
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onTradeAction(pos.symbol);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition"
                    >
                      Trade
                    </button>
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
