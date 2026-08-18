import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const MARKET_DISPLAY_NAMES: Record<string, { name: string; short: string }> = {
  "^GSPC": { name: "S&P 500", short: "S&P" },
  "^IXIC": { name: "NASDAQ", short: "NAS" },
  "^DJI": { name: "DOW JONES", short: "DOW" },
  "^VIX": { name: "VIX", short: "VIX" },
};

export function formatSymbolDisplay(symbol?: string | null): string {
  if (!symbol) return "";
  const upper = symbol.trim().toUpperCase();
  return MARKET_DISPLAY_NAMES[upper]?.name || upper;
}

export function formatSymbolShort(symbol?: string | null): string {
  if (!symbol) return "";
  const upper = symbol.trim().toUpperCase();
  if (MARKET_DISPLAY_NAMES[upper]) {
    return MARKET_DISPLAY_NAMES[upper].short;
  }
  const clean = upper.replace(/^[^a-zA-Z0-9]+/, "");
  return clean.slice(0, 3) || upper.slice(0, 3);
}
