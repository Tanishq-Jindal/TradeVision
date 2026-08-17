import React from "react";
import { CheckCircle2, XCircle, Clock, Zap } from "lucide-react";
import { ServiceHealth } from "@/types";

interface HealthBadgeProps {
  name: string;
  service?: ServiceHealth;
  isLoading?: boolean;
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({ name, service, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800 animate-pulse">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-slate-800" />
          <div className="space-y-1.5">
            <div className="h-4 w-24 bg-slate-800 rounded" />
            <div className="h-3 w-16 bg-slate-800/60 rounded" />
          </div>
        </div>
        <div className="h-6 w-16 bg-slate-800 rounded-full" />
      </div>
    );
  }

  const isOk = service?.status === "ok";
  const isDisabled = service?.status === "disabled" || service?.status === "not_configured";
  const latency = service?.latency_ms !== undefined && !isDisabled ? `${service.latency_ms} ms` : null;

  let icon = <CheckCircle2 className="w-5 h-5" />;
  let iconContainerClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  let statusText = "Healthy";
  let statusTextColor = "text-emerald-400";
  let badgeText = "Operational";
  let badgeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";

  if (isDisabled) {
    icon = <Zap className="w-5 h-5" />;
    iconContainerClass = "bg-blue-500/10 text-blue-400 border border-blue-500/20";
    statusText = "In-Memory Mode (Active)";
    statusTextColor = "text-blue-400";
    badgeText = "In-Memory";
    badgeClass = "bg-blue-500/10 text-blue-400 border border-blue-500/30";
  } else if (!isOk) {
    icon = <XCircle className="w-5 h-5" />;
    iconContainerClass = "bg-rose-500/10 text-rose-400 border border-rose-500/20";
    statusText = service?.error || "Degraded";
    statusTextColor = "text-rose-400";
    badgeText = "Unavailable";
    badgeClass = "bg-rose-500/10 text-rose-400 border border-rose-500/30";
  }

  return (
    <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700/80 transition-all shadow-sm">
      <div className="flex items-center space-x-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconContainerClass}`}>
          {icon}
        </div>
        <div>
          <h4 className="text-sm font-semibold text-slate-200">{name}</h4>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-xs font-medium ${statusTextColor}`}>
              {statusText}
            </span>
            {latency && (
              <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                <Clock className="w-3 h-3 text-slate-500" />
                {latency}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className={`px-2.5 py-1 rounded-full text-xs font-medium uppercase tracking-wider ${badgeClass}`}>
        {badgeText}
      </div>
    </div>
  );
};
