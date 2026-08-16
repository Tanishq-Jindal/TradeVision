"use client";

import React, { useState, useEffect } from "react";
import { CorrelationNetworkResponse } from "@/types";
import { api } from "@/lib/api";
import { Network, RefreshCw, Activity } from "lucide-react";

export const CorrelationWidget: React.FC = () => {
  const [data, setData] = useState<CorrelationNetworkResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchCorrelation = async () => {
    setLoading(true);
    try {
      const res = await api.getCorrelationNetwork();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCorrelation();
  }, []);

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Network className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Cross-Asset Correlation Network
          </h3>
        </div>
        <button
          onClick={fetchCorrelation}
          disabled={loading}
          className="text-slate-400 hover:text-white transition p-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading && !data ? (
        <div className="py-8 text-center text-xs text-slate-500 animate-pulse">
          Computing Pearson return correlations...
        </div>
      ) : (
        <div className="space-y-3">
          {/* Nodes Grid */}
          <div className="flex flex-wrap gap-2">
            {data?.nodes.map((n) => (
              <div
                key={n.id}
                className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs flex items-center gap-1.5"
              >
                <span className="font-bold text-white">{n.id}</span>
                <span className="text-[10px] text-slate-400">({n.sector})</span>
              </div>
            ))}
          </div>

          {/* Links / Matrix Breakdown */}
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 pt-1">
            Top Pairwise Correlations (|&rho;| &gt; 0.25):
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
            {data?.links.slice(0, 9).map((link, i) => {
              const isHighCorr = Math.abs(link.correlation) > 0.65;
              return (
                <div
                  key={i}
                  className="p-2 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs flex items-center justify-between"
                >
                  <span className="font-bold text-slate-200">
                    {link.source} &harr; {link.target}
                  </span>
                  <span
                    className={`font-mono text-[11px] font-bold ${
                      isHighCorr ? "text-amber-400" : "text-blue-400"
                    }`}
                  >
                    {link.correlation > 0 ? "+" : ""}
                    {link.correlation.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
