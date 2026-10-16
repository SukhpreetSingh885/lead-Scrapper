"use client";

import React, { useState, useEffect } from "react";
import { Settings, Shield, Globe2, Key, Database, RefreshCw, CheckCircle2, AlertTriangle } from "lucide-react";
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
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <Header
          title="Platform Settings & Compliance"
          subtitle="Provider adapters, data licensing constraints, and system connectivity."
        />
        <button
          onClick={fetchHealth}
          disabled={isLoading}
          className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
          title="Refresh Status"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Sourcing Provider Cards */}
      <div className="space-y-4">
        <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Data Sourcing & Discovery Adapters
        </h2>

        {/* Demo Provider */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <div className="font-bold text-sm text-slate-900 flex items-center space-x-2">
              <span>Deterministic Demo Provider</span>
              <Badge variant="demo">Free Testing Mode</Badge>
            </div>
            <Badge variant="success">Active</Badge>
          </div>
          <p className="text-slate-500">
            Provides realistic deterministic test fixtures labeled <code>[DEMO DATA]</code>. Allows full
            testing of the search form, job progress, contact enrichment, and CSV/Excel exports with zero
            paid API keys.
          </p>
        </div>

        {/* Google Places Adapter */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <div className="font-bold text-sm text-slate-900 flex items-center space-x-2">
              <Key className="w-4 h-4 text-blue-600" />
              <span>Google Places API Adapter</span>
            </div>
            {healthData?.live_providers?.google_places?.configured ? (
              <Badge variant="success">API Key Configured</Badge>
            ) : (
              <Badge variant="secondary">Unconfigured (Demo Active)</Badge>
            )}
          </div>
          <p className="text-slate-500">
            Official Google Places Text Search (New/v1) integration. Used strictly for compliant temporary
            discovery previews. Under Google Maps Platform terms, restricted from permanent export without
            independent licensing.
          </p>
          <div className="text-[11px] text-slate-400 font-mono">
            Environment variable: <code>GOOGLE_MAPS_API_KEY</code>
          </div>
        </div>

        {/* Google Custom Search Adapter */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <div className="font-bold text-sm text-slate-900 flex items-center space-x-2">
              <Key className="w-4 h-4 text-slate-400" />
              <span>Google Custom Search JSON API</span>
            </div>
            {healthData?.live_providers?.google_search?.configured ? (
              <Badge variant="success">Configured</Badge>
            ) : (
              <Badge variant="secondary">Disabled (Optional)</Badge>
            )}
          </div>
          <p className="text-slate-500">
            Authorized Search API adapter for discovering public business domain links. Never scrapes consumer HTML.
          </p>
          <div className="text-[11px] text-slate-400 font-mono">
            Environment variables: <code>GOOGLE_SEARCH_API_KEY</code>, <code>GOOGLE_SEARCH_CX</code>
          </div>
        </div>
      </div>

      {/* Safety & Boundary System Controls */}
      <div className="space-y-4 pt-2">
        <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Safety, SSRF Guard & Geographic Policies
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5">
            <div className="flex items-center space-x-2 font-bold text-slate-900">
              <Globe2 className="w-4 h-4 text-emerald-600" />
              <span>Geographic Boundary Policy</span>
            </div>
            <p className="text-slate-500 text-[11px]">
              Platform exclusively accepts and resolves locations within India. All international locations
              are rejected at API validation.
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5">
            <div className="flex items-center space-x-2 font-bold text-slate-900">
              <Shield className="w-4 h-4 text-emerald-600" />
              <span>SSRF & Network Safeguard</span>
            </div>
            <p className="text-slate-500 text-[11px]">
              Crawler strictly blocks loopback (127.0.0.1), private RFC1918 subnets (10/8, 172.16/12, 192.168/16),
              and cloud metadata (169.254.169.254).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

