"use client";

import React from "react";
import { Bell, Search, Shield, Globe2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export function Header({ title = "Dashboard", subtitle }: HeaderProps) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-xl font-bold text-slate-900 leading-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* Environment Badge */}
        <div className="hidden sm:flex items-center space-x-2 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-full text-xs text-slate-600">
          <Globe2 className="w-3.5 h-3.5 text-blue-500" />
          <span>India Scope Only</span>
        </div>

        <Badge variant="demo" className="hidden sm:inline-flex">
          Deterministic Demo Mode
        </Badge>

        <div className="flex items-center space-x-3 border-l border-slate-200 pl-4">
          <div className="w-8 h-8 rounded-full bg-slate-800 text-white font-medium text-xs flex items-center justify-center">
            AD
          </div>
          <div className="hidden md:block text-left text-xs">
            <div className="font-semibold text-slate-800">Admin User</div>
            <div className="text-slate-400">admin@indialeads.internal</div>
          </div>
        </div>
      </div>
    </header>
  );
}

