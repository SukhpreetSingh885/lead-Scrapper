"use client";

import React, { useEffect, useRef } from "react";
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
  MapPin,
  ShieldCheck,
  LogOut,
  X,
  ChevronLeft,
  ChevronRight,
  Menu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/auth-context";
import { useNav } from "@/context/nav-context";

export const navigationItems = [
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
  const { logout } = useAuth();
  const {
    isMobileOpen,
    closeMobile,
    isCollapsed,
    toggleCollapse,
  } = useNav();

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus the close button when mobile drawer opens
  useEffect(() => {
    if (isMobileOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isMobileOpen]);

  return (
    <>
      {/* =========================================================================
          1. PERSISTENT SIDEBAR (Desktop >= 1280px visible, Tablet collapsible)
         ========================================================================= */}
      <aside
        className={cn(
          "hidden md:flex flex-col h-screen bg-slate-900 text-slate-100 border-r border-slate-800 shrink-0 select-none overflow-hidden transition-all duration-200 z-30",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        {/* Brand header */}
        <div className="px-3.5 py-3.5 border-b border-slate-800 flex items-center justify-between shrink-0">
          <Link
            href="/dashboard"
            className={cn("flex items-center space-x-2.5", isCollapsed && "justify-center w-full space-x-0")}
            title="India Leads Platform"
          >
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 font-bold text-xs shrink-0">
              IL
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <span className="font-bold text-sm text-white block leading-tight truncate">
                  India Leads
                </span>
                <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold block truncate">
                  B2B SaaS Platform
                </span>
              </div>
            )}
          </Link>
          {!isCollapsed && (
            <span title="India Only Platform" className="text-xs">
              🇮🇳
            </span>
          )}
        </div>

        {/* Scope banner */}
        {!isCollapsed ? (
          <div className="px-4 py-1.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between shrink-0">
            <div className="flex items-center space-x-1.5 text-[11px] text-slate-300">
              <MapPin className="w-3 h-3 text-blue-400 shrink-0" />
              <span>India Exclusive</span>
            </div>
            <Badge
              variant="secondary"
              className="text-[9px] py-0 px-1 bg-emerald-950/60 text-emerald-400 border border-emerald-800/80"
            >
              LIVE
            </Badge>
          </div>
        ) : (
          <div className="py-1.5 bg-slate-950/60 border-b border-slate-800/80 flex justify-center shrink-0">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Live India Data" />
          </div>
        )}

        {/* Nav items */}
        <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto no-scrollbar [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          {navigationItems.map((item) => {
            const isActive =
              pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                title={item.name}
                className={cn(
                  "flex items-center text-xs font-medium rounded-lg transition-colors group",
                  isCollapsed ? "justify-center p-2.5" : "px-3 py-2",
                  isActive
                    ? "bg-blue-600 text-white shadow-sm font-semibold"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    !isCollapsed && "mr-2.5",
                    isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                  )}
                />
                {!isCollapsed && <span className="flex-1 truncate">{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Collapse toggle (Tablet / Desktop) */}
        <div className="px-2 py-1.5 border-t border-slate-800/80 shrink-0">
          <button
            onClick={toggleCollapse}
            className={cn(
              "w-full flex items-center text-xs font-medium rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors group",
              isCollapsed ? "justify-center p-2" : "px-3 py-1.5"
            )}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4 shrink-0 text-slate-400 group-hover:text-slate-200" />
            ) : (
              <>
                <ChevronLeft className="mr-2 h-4 w-4 shrink-0 text-slate-400 group-hover:text-slate-200" />
                <span className="text-[11px] text-slate-400 group-hover:text-slate-200">Collapse</span>
              </>
            )}
          </button>
        </div>

        {/* Logout Action */}
        <div className="px-2 py-1.5 border-t border-slate-800 shrink-0">
          <button
            onClick={() => logout()}
            className={cn(
              "w-full flex items-center text-xs font-medium rounded-lg text-slate-400 hover:bg-rose-950/40 hover:text-rose-300 transition-colors group",
              isCollapsed ? "justify-center p-2.5" : "px-3 py-2"
            )}
            title="Sign Out"
          >
            <LogOut
              className={cn(
                "h-4 w-4 shrink-0 text-slate-400 group-hover:text-rose-300 transition-colors",
                !isCollapsed && "mr-2.5"
              )}
            />
            {!isCollapsed && <span>Sign Out</span>}
          </button>
        </div>

        {/* Compliance footer info */}
        {!isCollapsed && (
          <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400 shrink-0">
            <div className="flex items-center space-x-1.5 text-emerald-400 font-medium mb-0.5">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              <span>Compliant Sourcing</span>
            </div>
            <p className="text-[10px] leading-relaxed text-slate-500">
              Strict provider terms, E.164 verification &amp; SSRF protection enabled.
            </p>
          </div>
        )}
      </aside>

      {/* =========================================================================
          2. MOBILE SLIDE-OUT DRAWER (< 768px with backdrop & keyboard/focus support)
         ========================================================================= */}
      {isMobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true" aria-label="Navigation Menu">
          {/* Backdrop overlay */}
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
            onClick={closeMobile}
            aria-hidden="true"
          />

          {/* Drawer container */}
          <div className="fixed inset-y-0 left-0 max-w-xs w-full bg-slate-900 text-slate-100 flex flex-col shadow-2xl border-r border-slate-800 z-50 animate-in slide-in-from-left duration-200">
            {/* Drawer Header */}
            <div className="px-4 py-3.5 border-b border-slate-800 flex items-center justify-between shrink-0">
              <Link href="/dashboard" onClick={closeMobile} className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 font-bold text-xs">
                  IL
                </div>
                <div>
                  <span className="font-bold text-sm text-white block leading-tight">
                    India Leads
                  </span>
                  <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">
                    B2B SaaS Platform
                  </span>
                </div>
              </Link>
              <button
                ref={closeButtonRef}
                onClick={closeMobile}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Close navigation menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scope banner */}
            <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-1.5 text-xs text-slate-300">
                <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span>India Exclusive 🇮🇳</span>
              </div>
              <Badge
                variant="secondary"
                className="text-[10px] py-0.5 px-1.5 bg-emerald-950/60 text-emerald-400 border border-emerald-800/80"
              >
                LIVE
              </Badge>
            </div>

            {/* Mobile Nav links */}
            <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto no-scrollbar">
              {navigationItems.map((item) => {
                const isActive =
                  pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={closeMobile}
                    className={cn(
                      "flex items-center px-3.5 py-2.5 text-sm font-medium rounded-lg transition-colors group",
                      isActive
                        ? "bg-blue-600 text-white shadow-sm font-semibold"
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

            {/* Logout Action */}
            <div className="px-3 py-2 border-t border-slate-800 shrink-0">
              <button
                onClick={() => {
                  closeMobile();
                  logout();
                }}
                className="w-full flex items-center px-3.5 py-2.5 text-sm font-medium rounded-lg text-slate-400 hover:bg-rose-950/40 hover:text-rose-300 transition-colors group"
              >
                <LogOut className="mr-3 h-4 w-4 shrink-0 text-slate-400 group-hover:text-rose-300 transition-colors" />
                <span>Sign Out</span>
              </button>
            </div>

            {/* Compliance footer info */}
            <div className="p-3.5 border-t border-slate-800 bg-slate-950/40 text-xs text-slate-400 shrink-0">
              <div className="flex items-center space-x-1.5 text-emerald-400 font-medium mb-1">
                <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                <span>Compliant Sourcing</span>
              </div>
              <p className="text-[11px] leading-relaxed text-slate-500">
                Strict provider terms, E.164 verification &amp; SSRF protection enabled.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
