"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { TrendingUp, Lock, Mail, ArrowRight, Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await login({ email, password });
      router.push("/");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to sign in. Please check your credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setEmail("demo@tradewise.cloud");
    setPassword("demo123");
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-blue-600/10 blur-[130px] rounded-full" />
        <div className="absolute -bottom-20 right-1/4 w-[400px] h-[300px] bg-emerald-600/5 blur-[120px] rounded-full" />
      </div>

      <div className="w-full max-w-md relative z-10 space-y-6">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <Link href="/" className="inline-flex items-center space-x-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">TradeWise</span>
          </Link>
          <h2 className="text-xl font-semibold text-slate-200">Welcome back</h2>
          <p className="text-xs text-slate-400">Sign in to manage your paper portfolio and AI intelligence</p>
        </div>

        {/* Demo Quick-Fill Banner */}
        <button
          type="button"
          onClick={handleFillDemo}
          className="w-full p-3.5 rounded-xl bg-gradient-to-r from-blue-950/40 via-indigo-950/40 to-slate-900/60 border border-blue-500/30 hover:border-blue-400/50 transition-all flex items-center justify-between text-left group"
        >
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-200 group-hover:text-blue-300 transition">
                One-Click Demo Account
              </div>
              <div className="text-[11px] text-slate-400">Pre-loaded with $100,000 virtual cash</div>
            </div>
          </div>
          <span className="text-xs font-medium text-blue-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
            Fill Demo <ArrowRight className="w-3.5 h-3.5" />
          </span>
        </button>

        {/* Form Card */}
        <div className="p-6 rounded-2xl bg-slate-950/80 border border-slate-800/90 backdrop-blur-xl shadow-2xl space-y-5">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start space-x-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Email address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 font-medium text-sm text-white shadow-lg shadow-blue-600/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>
        </div>

        {/* Footer Link */}
        <div className="text-center text-xs text-slate-400">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-blue-400 hover:text-blue-300 font-medium transition">
            Create an account ($100k free)
          </Link>
        </div>
      </div>
    </div>
  );
}
