"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Lock, Mail, ArrowRight, ShieldCheck, Eye, EyeOff, Loader2 } from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get("redirect") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    const formData = new URLSearchParams();
    formData.append("username", email.trim());
    formData.append("password", password);

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        credentials: "include",
        body: formData.toString(),
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error("Invalid email or password. Please verify your credentials.");
        } else if (res.status === 403) {
          throw new Error("This account is inactive. Please contact your organization administrator.");
        } else if (res.status >= 500) {
          throw new Error("Authentication server error (port 8001). Please check backend server logs.");
        }
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Authentication failed. Please try again.");
      }

      const data = await res.json();
      if (typeof window !== "undefined") {
        localStorage.setItem("indialeads_token", data.access_token);
      }

      // Redirect to the intended destination or dashboard
      const targetUrl = redirectPath.startsWith("/") ? redirectPath : "/dashboard";
      window.location.href = targetUrl;
    } catch (err: any) {
      if (err.name === "TypeError" && (err.message.includes("fetch") || err.message.includes("network") || err.message.includes("Failed"))) {
        setErrorMsg("Cannot connect to backend server. Please verify the FastAPI backend is running on port 8001.");
      } else {
        setErrorMsg(err.message || "Login failed");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white py-6 sm:py-8 px-5 sm:px-8 shadow-xl rounded-2xl border border-slate-200 space-y-5 w-full">
      {errorMsg && (
        <div className="p-3 sm:p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 leading-relaxed break-words">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-4 text-xs w-full">
        <div className="w-full">
          <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Email Address
          </label>
          <div className="relative w-full">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              required
              autoFocus
            />
          </div>
        </div>

        <div className="w-full">
          <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Password
          </label>
          <div className="relative w-full">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" />
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full pl-10 pr-10 py-2.5 rounded-lg border border-slate-300 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 p-1 focus:outline-none touch-manipulation min-w-[28px] min-h-[28px] flex items-center justify-center"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow transition-colors flex items-center justify-center space-x-2 disabled:opacity-60 min-h-[44px] touch-manipulation"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Signing in...</span>
            </>
          ) : (
            <>
              <span>Sign in to Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="pt-2 border-t border-slate-100 flex items-center justify-center space-x-1.5 text-[11px] text-slate-400 text-center leading-normal">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
        <span>Secure HttpOnly session with organization-level isolation</span>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-8 sm:py-12 px-4 sm:px-6 lg:px-8 w-full">
      <div className="w-full max-w-sm sm:max-w-md mx-auto text-center space-y-2">
        <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white text-xl font-bold mx-auto shadow-lg shadow-blue-500/30">
          IL
        </div>
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white break-words">
          India Leads Platform
        </h2>
        <p className="text-xs text-slate-400 break-words px-2">
          India-Only B2B Lead Generation &amp; Data Enrichment SaaS
        </p>
      </div>

      <div className="mt-6 sm:mt-8 w-full max-w-sm sm:max-w-md mx-auto">
        <Suspense fallback={<div className="bg-white p-8 rounded-2xl text-center text-xs text-slate-500">Loading login...</div>}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
