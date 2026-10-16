"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Users,
  Briefcase,
  CopyX,
  Upload,
  Download,
  Settings,
  Sparkles,
  MapPin,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const navigationItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Find Leads", href: "/search", icon: Search },
  { name: "All Leads", href: "/leads", icon: Users },
  { name: "Search Jobs", href: "/jobs", icon: Briefcase },
  { name: "Duplicate Review", href: "/duplicates", icon: CopyX },
  { name: "Import Data", href: "/imports", icon: Upload },
  { name: "Exports", href: "/exports", icon: Download },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col h-screen border-r border-slate-800 shrink-0 select-none">
      {/* Brand header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 font-bold">
            IL
          </div>
          <div>
            <span className="font-bold text-base text-white block leading-tight">
              India Leads
            </span>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
              B2B SaaS Platform
            </span>
          </div>
        </Link>
        <span title="India Only Platform" className="text-sm">🇮🇳</span>
      </div>

      {/* Scope banner */}
      <div className="px-4 py-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-1.5 text-xs text-slate-300">
          <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>India Exclusive</span>
        </div>
        <Badge variant="demo" className="text-[10px] py-0 px-1.5">
          TEST MODE
        </Badge>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors group",
                isActive
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                )}
              />
              <span className="flex-1">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Compliance footer info */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-xs text-slate-400">
        <div className="flex items-center space-x-1.5 text-emerald-400 font-medium mb-1">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Compliant Sourcing</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-500">
          Strict provider terms, E.164 verification & SSRF protection enabled.
        </p>
      </div>
    </aside>
  );
}

