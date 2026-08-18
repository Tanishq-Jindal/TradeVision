"use client";

import React, { useEffect, useRef } from "react";
import { createChart, CandlestickSeries, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";
import { CandleBar, Quote } from "@/types";
import { TrendingUp, TrendingDown, Clock } from "lucide-react";

interface PriceChartProps {
  symbol: string;
  quote?: Quote | null;
  candles: CandleBar[];
  isLoading?: boolean;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  symbol,
  quote,
  candles,
  isLoading,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: "#090d16" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "#1e293b",
      },
      timeScale: {
        borderColor: "#1e293b",
        timeVisible: true,
        secondsVisible: false,
      },
      height: 380,
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  // Update chart data whenever candles change
  useEffect(() => {
    if (candleSeriesRef.current && candles.length > 0) {
      const formattedData: CandlestickData<Time>[] = candles
        .map((c) => ({
          time: c.time as Time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
        .sort((a, b) => (Number(a.time) - Number(b.time)));

      candleSeriesRef.current.setData(formattedData);
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }
    }
  }, [candles]);

  const isPositive = quote ? (quote.d ?? 0) >= 0 : true;

  return (
    <div id="main-market-chart" className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-4">
      {/* Chart Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate-800/60">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center font-bold text-white tracking-wider">
            {symbol.slice(0, 3)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white tracking-tight">{symbol}</h3>
              {quote && (() => {
                const status = quote.market_status || "Closed";
                if (status === "Live") {
                  return (
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      LIVE MARKET DATA
                    </span>
                  );
                } else if (status === "Pre-Market") {
                  return (
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                      PRE-MARKET · REAL FEED
                    </span>
                  );
                } else if (status === "After-Hours") {
                  return (
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                      AFTER-HOURS · REAL FEED
                    </span>
                  );
                } else {
                  return (
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700/60 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                      MARKET CLOSED · REAL FEED
                    </span>
                  );
                }
              })()}
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span>Open: <strong className="text-slate-200">${quote?.o?.toFixed(2) || "---"}</strong></span>
              <span>High: <strong className="text-slate-200">${quote?.h?.toFixed(2) || "---"}</strong></span>
              <span>Low: <strong className="text-slate-200">${quote?.l?.toFixed(2) || "---"}</strong></span>
            </div>
          </div>
        </div>

        {quote && (
          <div className="text-right">
            <div className="text-2xl font-black text-white font-mono">
              ${(quote.c ?? quote.current_price ?? 0).toFixed(2)}
            </div>
            <div
              className={`flex items-center justify-end gap-1 text-xs font-semibold ${
                isPositive ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {isPositive ? (
                <TrendingUp className="w-3.5 h-3.5" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" />
              )}
              <span>
                {isPositive ? "+" : ""}
                {(quote.d ?? quote.change ?? 0).toFixed(2)} ({isPositive ? "+" : ""}
                {(quote.dp ?? quote.change_percent ?? 0).toFixed(2)}%)
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Chart Canvas */}
      <div className="relative w-full h-[380px] rounded-xl overflow-hidden bg-[#090d16]">
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center z-10">
            <div className="text-xs text-slate-400 animate-pulse flex items-center gap-2">
              <Clock className="w-4 h-4 animate-spin text-blue-400" />
              Loading chart data...
            </div>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>
    </div>
  );
};
