"use client";

import React from "react";
import { SwarmConsensusResponse } from "@/types";
import { Users, TrendingUp, TrendingDown, ShieldAlert, Sparkles, CheckCircle2, AlertTriangle } from "lucide-react";

interface SwarmConsensusWidgetProps {
  swarm?: SwarmConsensusResponse | null;
  isLoading?: boolean;
}

export const SwarmConsensusWidget: React.FC<SwarmConsensusWidgetProps> = ({ swarm, isLoading }) => {
  if (isLoading || !swarm) {
    return (
      <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800/80 backdrop-blur-xl animate-pulse space-y-4">
        <div className="h-4 bg-slate-900 rounded w-1/3" />
        <div className="h-20 bg-slate-900 rounded-xl" />
        <div className="grid grid-cols-2 gap-2">
          <div className="h-16 bg-slate-900 rounded-lg" />
          <div className="h-16 bg-slate-900 rounded-lg" />
        </div>
      </div>
    );
  }

  const isBullish = swarm.consensus_score > 0.15;
  const isBearish = swarm.consensus_score < -0.15;

  return (
    <div className="rounded-2xl bg-slate-950/80 border border-slate-800/80 p-5 backdrop-blur-xl shadow-xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Multi-Agent Swarm Deliberation
          </h3>
        </div>
        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
          {swarm.agreement_percentage}% Agreement
        </span>
      </div>

      {/* Consensus Banner */}
      <div
        className={`p-4 rounded-xl border flex items-center justify-between ${
          isBullish
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
            : isBearish
            ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
            : "bg-blue-500/10 border-blue-500/30 text-blue-300"
        }`}
      >
        <div className="space-y-0.5">
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-80">
            Consensus Signal
          </div>
          <div className="text-xl font-black flex items-center gap-1.5">
            {isBullish ? (
              <TrendingUp className="w-5 h-5" />
            ) : isBearish ? (
              <TrendingDown className="w-5 h-5" />
            ) : (
              <CheckCircle2 className="w-5 h-5" />
            )}
            <span>{swarm.consensus_signal.replace("_", " ")}</span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-[10px] font-bold uppercase tracking-wider opacity-80">
            Score (-1 to +1)
          </div>
          <div className="font-mono text-lg font-bold">
            {swarm.consensus_score > 0 ? "+" : ""}
            {swarm.consensus_score.toFixed(2)}
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-300 italic border-l-2 border-purple-500/60 pl-3 leading-relaxed">
        &ldquo;{swarm.summary}&rdquo;
      </p>

      {/* 4 Agent Opinions */}
      <div className="space-y-2 pt-1">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Agent Committee Deliberation:
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {swarm.agents.map((agent, i) => {
            const isAgentBull = agent.signal === "BULLISH";
            const isAgentBear = agent.signal === "BEARISH";
            return (
              <div
                key={i}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">{agent.agent_name}</span>
                  <span
                    className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                      isAgentBull
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : isAgentBear
                        ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {agent.signal}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">{agent.reasoning}</p>
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
                  <span>Confidence: {(agent.confidence * 100).toFixed(0)}%</span>
                  <span>Weight: {(agent.recommended_weight * 100).toFixed(0)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
