"use client";

import React, { useState } from "react";
import { LogOut, Globe2, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/auth-context";

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export function Header({ title = "Dashboard", subtitle }: HeaderProps) {
  const { user, logout, isLoading } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await logout();
  };

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      const parts = name.trim().split(" ");
      if (parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      }
      return name.slice(0, 2).toUpperCase();
    }
    if (email) {
      return email.slice(0, 2).toUpperCase();
    }
    return "U";
  };

  return (
    <header className="min-h-14 sm:min-h-16 bg-white border border-slate-200 rounded-xl px-4 py-3 sm:px-6 sm:py-3.5 flex items-center justify-between shrink-0 shadow-2xs gap-3">
      <div className="min-w-0 flex-1">
        <h1 className="text-lg sm:text-xl font-bold text-slate-900 leading-tight truncate">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-slate-500 mt-0.5 line-clamp-1 sm:line-clamp-none">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
        {/* Environment Badge (visible on lg screens) */}
        <div className="hidden lg:flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-full text-xs text-slate-600 shrink-0">
          <Globe2 className="w-3.5 h-3.5 text-blue-500" />
          <span>India Scope Only</span>
        </div>

        {/* Live Badge (visible on xl screens) */}
        <Badge
          variant="secondary"
          className="hidden xl:inline-flex bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs shrink-0"
        >
          Live Data Extraction
        </Badge>

        {/* User Profile & Sign Out */}
        <div className="flex items-center space-x-2 sm:space-x-3 pl-2 sm:pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-800 text-white font-medium text-xs flex items-center justify-center shrink-0">
            {getInitials(user?.full_name, user?.email)}
          </div>
          <div className="hidden md:block text-left text-xs max-w-[130px] truncate">
            <div className="font-semibold text-slate-800 truncate">
              {user?.full_name || (isLoading ? "Loading..." : "User")}
            </div>
            <div className="text-slate-400 text-[11px] truncate">
              {user?.email || (isLoading ? "..." : "")}
            </div>
          </div>

          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            title="Log out of session"
            className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-md border border-slate-200 hover:bg-rose-50 hover:border-rose-300 text-slate-600 hover:text-rose-700 text-xs font-medium transition-colors disabled:opacity-50 shrink-0"
          >
            {isLoggingOut ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <LogOut className="w-3.5 h-3.5 text-slate-500 hover:text-rose-600" />
            )}
            <span className="hidden sm:inline">
              {isLoggingOut ? "Signing out..." : "Sign Out"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
