"use client";

import React, { useState, useEffect } from "react";
import { Quote, Position } from "@/types";
import { api, ApiError } from "@/lib/api";
import { formatSymbolDisplay, formatSymbolShort } from "@/lib/utils";
import { ArrowDownLeft, ArrowUpRight, DollarSign, Loader2, AlertCircle, CheckCircle2, X } from "lucide-react";

interface OrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  quote?: Quote | null;
  cashBalance: number;
  existingPosition?: Position | null;
  onTradeSuccess: () => void;
}

export const OrderModal: React.FC<OrderModalProps> = ({
  isOpen,
  onClose,
  symbol,
  quote,
  cashBalance,
  existingPosition,
  onTradeSuccess,
}) => {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState<string>("10");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    setSuccessMsg(null);
  }, [symbol, isOpen, side]);

  if (!isOpen) return null;

  const price = quote?.c || 100.0;
  const numQty = parseFloat(quantity) || 0;
  const totalValue = numQty * price;
  const maxBuyQty = Math.floor(cashBalance / price);
  const heldShares = existingPosition?.quantity || 0;

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (numQty <= 0) {
      setError("Please enter a valid share quantity.");
      return;
    }

    if (side === "BUY" && totalValue > cashBalance) {
      setError(`Insufficient cash. Order requires $${totalValue.toFixed(2)}.`);
      return;
    }

    if (side === "SELL" && numQty > heldShares) {
      setError(`You only hold ${heldShares} shares of ${symbol}.`);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      if (side === "BUY") {
        await api.buyStock(symbol, numQty);
        setSuccessMsg(`Successfully bought ${numQty} shares of ${symbol}!`);
      } else {
        await api.sellStock(symbol, numQty);
        setSuccessMsg(`Successfully sold ${numQty} shares of ${symbol}!`);
      }
      onTradeSuccess();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to execute trade. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-slate-950 border border-slate-800/90 rounded-2xl p-6 shadow-2xl space-y-5 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
            {formatSymbolShort(symbol)}
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Execute Paper Trade: {formatSymbolDisplay(symbol)}</h3>
            <div className="text-xs text-slate-400 font-mono">
              Market Price: <strong className="text-slate-200">${price.toFixed(2)}</strong>
            </div>
          </div>
        </div>

        {/* Side Selector Tabs */}
        <div className="grid grid-cols-2 p-1 rounded-xl bg-slate-900 border border-slate-800">
          <button
            type="button"
            onClick={() => setSide("BUY")}
            className={`py-2 text-xs font-bold rounded-lg transition ${
              side === "BUY"
                ? "bg-emerald-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Buy {formatSymbolDisplay(symbol)}
          </button>
          <button
            type="button"
            onClick={() => setSide("SELL")}
            className={`py-2 text-xs font-bold rounded-lg transition ${
              side === "SELL"
                ? "bg-rose-500 text-white shadow-md"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Sell {formatSymbolDisplay(symbol)}
          </button>
        </div>

        {/* Notifications */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleExecute} className="space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="font-medium text-slate-300">Number of Shares</label>
              <span className="text-slate-400">
                {side === "BUY" ? (
                  <>Max: <strong className="text-slate-200">{maxBuyQty}</strong> shares</>
                ) : (
                  <>Held: <strong className="text-slate-200">{heldShares}</strong> shares</>
                )}
              </span>
            </div>
            <input
              type="number"
              min="0.01"
              step="any"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>

          {/* Quick presets */}
          <div className="flex gap-2">
            {[0.25, 0.5, 0.75, 1.0].map((pct) => (
              <button
                key={pct}
                type="button"
                onClick={() => {
                  if (side === "BUY") {
                    setQuantity((maxBuyQty * pct).toFixed(2));
                  } else {
                    setQuantity((heldShares * pct).toFixed(2));
                  }
                }}
                className="flex-1 py-1 text-[11px] font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition"
              >
                {pct * 100}%
              </button>
            ))}
          </div>

          {/* Order Summary */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Estimated Order Value</span>
              <span className="font-mono text-slate-200 font-bold">${totalValue.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Available Cash</span>
              <span className="font-mono text-emerald-400 font-bold">${cashBalance.toFixed(2)}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || numQty <= 0}
            className={`w-full py-2.5 px-4 rounded-xl font-bold text-sm text-white shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50 ${
              side === "BUY"
                ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20"
                : "bg-rose-600 hover:bg-rose-500 shadow-rose-600/20"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Executing Order...
              </>
            ) : side === "BUY" ? (
              `Buy ${numQty} ${symbol} ($${totalValue.toFixed(2)})`
            ) : (
              `Sell ${numQty} ${symbol} ($${totalValue.toFixed(2)})`
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
