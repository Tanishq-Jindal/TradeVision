"use client";

import React, { useState, useEffect } from "react";
import { Trade } from "@/types";
import { formatSymbolDisplay } from "@/lib/utils";
import { History, ArrowDownLeft, ArrowUpRight, ChevronLeft, ChevronRight } from "lucide-react";

interface RecentTradesProps {
  trades: Trade[];
}

const PAGE_SIZE = 10;

export const RecentTrades: React.FC<RecentTradesProps> = ({ trades }) => {
  const [currentPage, setCurrentPage] = useState(1);

  const totalTransactions = trades.length;
  const totalPages = Math.ceil(totalTransactions / PAGE_SIZE);

  // Automatically keep currentPage within the valid range when transactions list changes
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    } else if (currentPage < 1) {
      setCurrentPage(1);
    }
  }, [totalTransactions, totalPages, currentPage]);

  if (totalTransactions === 0) {
    return null;
  }

  const effectivePage = Math.min(Math.max(1, currentPage), Math.max(1, totalPages));
  const startIndex = (effectivePage - 1) * PAGE_SIZE;
  const endIndex = startIndex + PAGE_SIZE;
  const displayedTrades = trades.slice(startIndex, endIndex);

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Trade Execution Log
          </h3>
        </div>
        <span className="text-xs text-slate-500">
          {totalTransactions} Executed {totalPages > 1 ? `· Page ${effectivePage} of ${totalPages}` : ""}
        </span>
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
            {displayedTrades.map((t) => {
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
                  <td className="py-2.5 px-3 font-bold text-white">{formatSymbolDisplay(t.symbol)}</td>
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

      {/* Pagination Controls - only rendered if totalPages > 1 */}
      {totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/60 text-xs">
          <div className="text-slate-400">
            Showing <span className="font-semibold text-slate-200">{startIndex + 1}</span> to{" "}
            <span className="font-semibold text-slate-200">
              {Math.min(endIndex, totalTransactions)}
            </span>{" "}
            of <span className="font-semibold text-slate-200">{totalTransactions}</span> entries
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={effectivePage <= 1}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white disabled:opacity-40 disabled:hover:bg-slate-900/80 disabled:hover:text-slate-300 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>

            <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 font-medium font-mono text-xs">
              Page {effectivePage} of {totalPages}
            </span>

            <button
              type="button"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={effectivePage >= totalPages}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white disabled:opacity-40 disabled:hover:bg-slate-900/80 disabled:hover:text-slate-300 disabled:cursor-not-allowed transition"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
