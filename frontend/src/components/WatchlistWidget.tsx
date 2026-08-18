"use client";

import React, { useState } from "react";
import { WatchlistItem, SymbolSearchResult } from "@/types";
import { api } from "@/lib/api";
import { formatSymbolDisplay } from "@/lib/utils";
import { TrendingUp, TrendingDown, Search, Plus, Trash2, Loader2, Bookmark } from "lucide-react";

interface WatchlistWidgetProps {
  items: WatchlistItem[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  onWatchlistChanged: () => void;
}

export const WatchlistWidget: React.FC<WatchlistWidgetProps> = ({
  items,
  selectedSymbol,
  onSelectSymbol,
  onWatchlistChanged,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SymbolSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [addingSymbol, setAddingSymbol] = useState(false);

  const handleSearch = async (val: string) => {
    setSearchQuery(val);
    if (!val.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const results = await api.searchSymbols(val);
      setSearchResults(results);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddSymbol = async (sym: string) => {
    setAddingSymbol(true);
    try {
      await api.addToWatchlist(sym);
      onWatchlistChanged();
      setSearchQuery("");
      setSearchResults([]);
    } catch (e) {
      console.error(e);
    } finally {
      setAddingSymbol(false);
    }
  };

  const handleRemoveSymbol = async (sym: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.removeFromWatchlist(sym);
      onWatchlistChanged();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-4">
      {/* Header & Search */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bookmark className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Watchlist</h3>
        </div>
        <span className="text-xs text-slate-500">{items.length} Tracked</span>
      </div>

      {/* Autocomplete Search input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
          <Search className="w-3.5 h-3.5" />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search ticker (e.g. AAPL, NVDA)..."
          className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        />

        {/* Dropdown Results */}
        {searchResults.length > 0 && (
          <div className="absolute top-full mt-1 left-0 right-0 z-30 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl divide-y divide-slate-800/60 max-h-56 overflow-y-auto">
            {searchResults.map((res) => (
              <div
                key={res.symbol}
                onClick={() => handleAddSymbol(res.symbol)}
                className="p-2.5 hover:bg-slate-800/80 flex items-center justify-between cursor-pointer transition text-xs"
              >
                <div>
                  <span className="font-bold text-white">{formatSymbolDisplay(res.symbol)}</span>
                  <span className="ml-2 text-[11px] text-slate-400">{res.description}</span>
                </div>
                <button className="px-2 py-0.5 rounded bg-blue-600/20 text-blue-400 text-[10px] font-bold uppercase hover:bg-blue-600 hover:text-white transition">
                  + Add
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Items List */}
      <div className="space-y-1.5 max-h-[380px] overflow-y-auto pr-1">
        {items.map((item) => {
          const isSelected = item.symbol === selectedSymbol;
          const isPositive = item.change >= 0;

          return (
            <div
              key={item.id}
              onClick={() => onSelectSymbol(item.symbol)}
              className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition ${
                isSelected
                  ? "bg-blue-600/10 border-blue-500/40 shadow-sm"
                  : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700/80 hover:bg-slate-900"
              }`}
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-sm text-white">{formatSymbolDisplay(item.symbol)}</span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />}
                </div>
                <div className="text-[11px] text-slate-400 truncate max-w-[120px]">{item.name}</div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="font-mono text-xs font-bold text-slate-200">
                    ${item.price.toFixed(2)}
                  </div>
                  <div
                    className={`text-[11px] font-semibold flex items-center justify-end gap-0.5 ${
                      isPositive ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isPositive ? "+" : ""}
                    {item.change_pct.toFixed(2)}%
                  </div>
                </div>

                <button
                  onClick={(e) => handleRemoveSymbol(item.symbol, e)}
                  title="Remove from watchlist"
                  className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
