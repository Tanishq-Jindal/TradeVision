"use client";

import React, { useState, useEffect } from "react";
import { AutopilotStatusResponse, AutopilotConfig } from "@/types";
import { api } from "@/lib/api";
import { Zap, ShieldCheck, ShieldAlert, Sliders, CheckCircle2, History, Loader2 } from "lucide-react";

export const AutopilotWidget: React.FC = () => {
  const [status, setStatus] = useState<AutopilotStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await api.getAutopilotStatus();
      setStatus(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleToggle = async () => {
    if (!status) return;
    setSaving(true);
    try {
      const updatedConfig: AutopilotConfig = {
        ...status.config,
        enabled: !status.active,
      };
      const res = await api.updateAutopilotConfig(updatedConfig);
      setStatus((prev) => (prev ? { ...prev, active: !prev.active, config: { ...prev.config, ...res } } : null));
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (loading || !status) {
    return (
      <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800/80 animate-pulse space-y-4">
        <div className="h-4 bg-slate-900 rounded w-1/3" />
        <div className="h-24 bg-slate-900 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Zap className={`w-4 h-4 ${status.active ? "text-emerald-400" : "text-slate-500"}`} />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Guardrailed Autopilot
          </h3>
        </div>
        <button
          onClick={handleToggle}
          disabled={saving}
          className={`px-3 py-1 rounded-full text-xs font-bold uppercase transition flex items-center gap-1.5 ${
            status.active
              ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
              : "bg-slate-800 hover:bg-slate-700 text-slate-300"
          }`}
        >
          {saving ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : status.active ? (
            "ACTIVE"
          ) : (
            "DISABLED"
          )}
        </button>
      </div>

      {/* Guardrails Parameters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] text-slate-400 font-semibold uppercase">Max Allocation</div>
          <div className="font-mono text-sm font-bold text-slate-200">
            {status.config.max_trade_allocation_pct}%
          </div>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] text-slate-400 font-semibold uppercase">Stop Loss Cutoff</div>
          <div className="font-mono text-sm font-bold text-rose-400">
            -{status.config.stop_loss_pct}%
          </div>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] text-slate-400 font-semibold uppercase">Take Profit Target</div>
          <div className="font-mono text-sm font-bold text-emerald-400">
            +{status.config.take_profit_pct}%
          </div>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] text-slate-400 font-semibold uppercase">Min Swarm Conf.</div>
          <div className="font-mono text-sm font-bold text-blue-400">
            {(status.config.min_confidence_threshold * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Autonomous Activity Log */}
      <div className="space-y-2">
        <div className="flex items-center space-x-1.5 text-xs text-slate-400">
          <History className="w-3.5 h-3.5" />
          <span className="font-semibold uppercase text-[10px] tracking-wider">
            Autonomous Actions Log ({status.recent_actions.length})
          </span>
        </div>

        {status.recent_actions.length === 0 ? (
          <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/60 text-center text-xs text-slate-500">
            No autonomous actions triggered yet. Autopilot continuously monitors risk guardrails and high-confidence swarm triggers.
          </div>
        ) : (
          <div className="space-y-1.5 max-h-36 overflow-y-auto">
            {status.recent_actions.map((act, i) => (
              <div
                key={i}
                className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs flex items-center justify-between"
              >
                <div>
                  <span className="font-bold text-white">{act.action_type.replace("AUTONOMOUS_", "")}</span>{" "}
                  <span className="text-slate-400">
                    ({act.quantity} shares of {act.symbol} @ ${act.price.toFixed(2)})
                  </span>
                  <div className="text-[11px] text-slate-400">{act.reason}</div>
                </div>
                <span className="font-mono text-[10px] text-slate-500">
                  {new Date(typeof act.timestamp === "number" ? act.timestamp * 1000 : act.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
