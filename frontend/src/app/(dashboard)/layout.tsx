"use client";

import React from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { AuthProvider, useAuth } from "@/context/auth-context";
import { NavProvider, useNav } from "@/context/nav-context";
import { Menu, Globe2 } from "lucide-react";
import Link from "next/link";

function DashboardLayoutContent({ children }: { children: React.ReactNode }) {
  const { toggleMobile } = useNav();
  const { user } = useAuth();

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
    return "IL";
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 w-full max-w-full">
      {/* Desktop / Tablet Sidebar & Mobile Drawer Component */}
      <Sidebar />

      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        {/* Mobile Top Navigation Bar (< 768px) */}
        <header className="md:hidden h-14 bg-slate-900 text-white border-b border-slate-800 px-3.5 flex items-center justify-between shrink-0 z-20">
          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={toggleMobile}
              className="p-1.5 -ml-1 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <Link href="/dashboard" className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                IL
              </div>
              <span className="font-bold text-sm tracking-tight">India Leads</span>
              <span className="text-xs">🇮🇳</span>
            </Link>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[10px] bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 px-1.5 py-0.5 rounded font-mono font-medium">
              LIVE
            </span>
            <div className="w-7 h-7 rounded-full bg-slate-800 text-white font-medium text-xs flex items-center justify-center border border-slate-700">
              {getInitials(user?.full_name, user?.email)}
            </div>
          </div>
        </header>

        {/* Main content scroll container with responsive padding */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-3.5 sm:p-5 md:p-6 lg:p-8 min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <NavProvider>
        <DashboardLayoutContent>{children}</DashboardLayoutContent>
      </NavProvider>
    </AuthProvider>
  );
}
