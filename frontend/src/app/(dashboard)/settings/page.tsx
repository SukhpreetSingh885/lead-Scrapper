"use client";

import React, { useState, useEffect } from "react";
import { Globe2, Key, Shield, RefreshCw } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";

export default function SettingsPage() {
  const [healthData, setHealthData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchHealth = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient<any>("/api/v1/health");
      setHealthData(data);
    } catch {
      setHealthData(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-5 sm:space-y-6 max-w-4xl mx-auto w-full min-w-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <Header
            title="Platform Settings &amp; Compliance"
            subtitle="Provider adapters, data licensing constraints, and system connectivity."
          />
        </div>
        <button
          onClick={fetchHealth}
          disabled={isLoading}
          className="p-2.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors self-end sm:self-center shrink-0 touch-manipulation min-w-[40px] min-h-[40px] flex items-center justify-center"
          title="Refresh Status"
          aria-label="Refresh Status"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Sourcing Provider Cards */}
      <div className="space-y-4">
        <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Data Sourcing &amp; Discovery Adapters
        </h2>

        {/* OpenStreetMap Overpass Provider */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-2 text-xs min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-bold text-sm text-slate-900 flex flex-wrap items-center gap-2">
              <Globe2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>OpenStreetMap Overpass API Provider</span>
              <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px]">Live Real Data</Badge>
            </div>
            <Badge variant="success" className="text-[10px]">Primary Active</Badge>
          </div>
          <p className="text-slate-500 leading-relaxed">
            Real commercial business discovery across India powered by the Overpass API under the Open Data Commons Open Database License (ODbL 1.0).
            Zero API key required. Supports nodes, ways, and relations with coordinate radius resolution and full contact enrichment.
          </p>
        </div>

        {/* Google Places Adapter */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-2 text-xs min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-bold text-sm text-slate-900 flex items-center space-x-2">
              <Key className="w-4 h-4 text-blue-600 shrink-0" />
              <span>Google Places API Adapter</span>
            </div>
            {healthData?.live_providers?.google_places?.configured ? (
              <Badge variant="success" className="text-[10px]">API Key Configured</Badge>
            ) : (
              <Badge variant="secondary" className="text-[10px]">Unconfigured (Demo Active)</Badge>
            )}
          </div>
          <p className="text-slate-500 leading-relaxed">
            Official Google Places Text Search (New/v1) integration. Used strictly for compliant temporary
            discovery previews. Under Google Maps Platform terms, restricted from permanent export without
            independent licensing.
          </p>
          <div className="text-[11px] text-slate-400 font-mono break-all">
            Environment variable: <code>GOOGLE_MAPS_API_KEY</code>
          </div>
        </div>

        {/* Google Custom Search Adapter */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-2 text-xs min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-bold text-sm text-slate-900 flex items-center space-x-2">
              <Key className="w-4 h-4 text-slate-400 shrink-0" />
              <span>Google Custom Search JSON API</span>
            </div>
            {healthData?.live_providers?.google_search?.configured ? (
              <Badge variant="success" className="text-[10px]">Configured</Badge>
            ) : (
              <Badge variant="secondary" className="text-[10px]">Disabled (Optional)</Badge>
            )}
          </div>
          <p className="text-slate-500 leading-relaxed">
            Authorized Search API adapter for discovering public business domain links. Never scrapes consumer HTML.
          </p>
          <div className="text-[11px] text-slate-400 font-mono break-all">
            Environment variables: <code>GOOGLE_SEARCH_API_KEY</code>, <code>GOOGLE_SEARCH_CX</code>
          </div>
        </div>
      </div>

      {/* Safety & Boundary System Controls */}
      <div className="space-y-4 pt-2">
        <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Safety, SSRF Guard &amp; Geographic Policies
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-xs">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5 min-w-0">
            <div className="flex items-center space-x-2 font-bold text-slate-900">
              <Globe2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Geographic Boundary Policy</span>
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Platform exclusively accepts and resolves locations within India. All international locations
              are rejected at API validation.
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5 min-w-0">
            <div className="flex items-center space-x-2 font-bold text-slate-900">
              <Shield className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>SSRF &amp; Network Safeguard</span>
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Crawler strictly blocks loopback (127.0.0.1), private RFC1918 subnets (10/8, 172.16/12, 192.168/16),
              and cloud metadata (169.254.169.254).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
