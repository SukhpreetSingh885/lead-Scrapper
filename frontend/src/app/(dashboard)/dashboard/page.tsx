"use client";

import React from "react";
import Link from "next/link";
import {
  Users,
  Smartphone,
  Mail,
  Globe,
  MessageSquare,
  CopyX,
  Briefcase,
  CheckCircle,
  Search,
  Upload,
  Download,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { useDashboardMetrics } from "@/hooks/use-leads";
import { useDiscoveryJobs } from "@/hooks/use-jobs";

export default function DashboardPage() {
  const { data: metrics, isLoading: isMetricsLoading } = useDashboardMetrics();
  const { data: jobsData } = useDiscoveryJobs(1, 5);

  const stats = [
    {
      label: "Total Unique Leads",
      value: metrics?.total_unique_leads ?? 0,
      icon: Users,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      href: "/leads",
    },
    {
      label: "Valid Mobile (+91)",
      value: metrics?.leads_with_mobile ?? 0,
      icon: Smartphone,
      color: "text-emerald-600",
      bgColor: "bg-emerald-50",
      href: "/leads?has_mobile=true",
    },
    {
      label: "Public Business Emails",
      value: metrics?.leads_with_email ?? 0,
      icon: Mail,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
      href: "/leads?has_email=true",
    },
    {
      label: "Active Websites",
      value: metrics?.leads_with_website ?? 0,
      icon: Globe,
      color: "text-sky-600",
      bgColor: "bg-sky-50",
      href: "/leads?has_website=true",
    },
    {
      label: "Business WhatsApp",
      value: metrics?.leads_with_whatsapp ?? 0,
      icon: MessageSquare,
      color: "text-teal-600",
      bgColor: "bg-teal-50",
      href: "/leads?has_whatsapp=true",
    },
    {
      label: "Duplicate Candidates",
      value: metrics?.duplicate_candidates ?? 0,
      icon: CopyX,
      color: "text-amber-600",
      bgColor: "bg-amber-50",
      href: "/duplicates",
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <Header
        title="B2B Intelligence Dashboard"
        subtitle="Real-time business lead discovery, branch deduplication, and contact enrichment metrics."
      />

      {/* Demo Mode Notice Banner */}
      {metrics?.is_demo_mode_active && (
        <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
            <span>
              <strong>Deterministic Free Testing Mode Active:</strong> Current metrics and leads
              contain deterministic offline test fixtures labeled <code>[DEMO DATA]</code>. No paid API
              credentials required for local testing.
            </span>
          </div>
          <Link
            href="/search"
            className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md font-semibold text-xs transition-colors shrink-0"
          >
            Run Test Search
          </Link>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((stat, idx) => (
          <Link
            key={idx}
            href={stat.href}
            className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:border-blue-300 transition-all group"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider line-clamp-1">
                {stat.label}
              </span>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {isMetricsLoading ? "..." : stat.value}
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Launch Action Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center sm:text-left">
          <h2 className="text-xl font-bold">Discover Leads in Any Indian City</h2>
          <p className="text-sm text-blue-100 max-w-xl">
            Target Salons, Restaurants, IT Companies, or Agencies in Mohali, Chandigarh, Delhi,
            Ludhiana, Bengaluru, or any Indian district with automated branch deduplication.
          </p>
        </div>
        <Link
          href="/search"
          className="px-5 py-3 bg-white text-blue-700 font-bold rounded-xl text-sm shadow hover:bg-blue-50 transition-colors flex items-center space-x-2 shrink-0"
        >
          <Search className="w-4 h-4" />
          <span>Launch Search</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Two Column Layout: Recent Jobs & Sourcing Quick Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Search Jobs */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center">
              <Briefcase className="w-4 h-4 text-blue-600 mr-2" />
              Recent Discovery Jobs
            </h3>
            <Link
              href="/jobs"
              className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1"
            >
              <span>View all jobs</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-100">
            {jobsData?.items && jobsData.items.length > 0 ? (
              jobsData.items.map((job) => (
                <div key={job.id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">
                      {job.category} in {job.resolved_city}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Discovered {job.total_discovered} • Inserted {job.total_inserted} • Duplicates Flagged {job.total_duplicates_flagged}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge
                      variant={
                        job.status === "completed"
                          ? "success"
                          : job.status === "running"
                          ? "warning"
                          : "secondary"
                      }
                      className="text-[10px] uppercase"
                    >
                      {job.status}
                    </Badge>
                    <Link
                      href={`/jobs?active=${job.id}`}
                      className="p-1 text-slate-400 hover:text-blue-600"
                    >
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                No discovery jobs created yet. Click "Launch Search" to start one.
              </div>
            )}
          </div>
        </div>

        {/* System & Sourcing Provenance Info */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-3">
            System & Data Provenance
          </h3>

          <div className="space-y-3 text-xs text-slate-600">
            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="font-semibold text-slate-800 mb-1">Geographic Boundary</div>
              <p className="text-[11px] text-slate-500">
                Strictly validated for Republic of India. Non-Indian locations are rejected automatically.
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="font-semibold text-slate-800 mb-1">E.164 Phone Normalization</div>
              <p className="text-[11px] text-slate-500">
                Normalized with Google's <code>libphonenumber</code> for India (+91 prefix, mobile vs landline).
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="font-semibold text-slate-800 mb-1">Branch-Level Deduplication</div>
              <p className="text-[11px] text-slate-500">
                Multi-stage RapidFuzz & database matching preserves distinct branches (Phase 7 vs Phase 3B2).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

