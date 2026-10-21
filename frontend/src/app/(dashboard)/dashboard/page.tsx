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
    <div className="space-y-5 sm:space-y-6 max-w-7xl mx-auto w-full min-w-0">
      <Header
        title="B2B Intelligence Dashboard"
        subtitle="Real-time business lead discovery, branch deduplication, and contact enrichment metrics."
      />

      {/* Demo Mode Notice Banner */}
      {metrics?.is_demo_mode_active && (
        <div className="p-3.5 sm:p-4 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-start sm:items-center space-x-2.5">
            <Sparkles className="w-4 h-4 text-purple-600 shrink-0 mt-0.5 sm:mt-0" />
            <span className="leading-relaxed">
              <strong>Deterministic Free Testing Mode Active:</strong> Current metrics and leads
              contain deterministic offline test fixtures labeled <code>[DEMO DATA]</code>. No paid API
              credentials required for local testing.
            </span>
          </div>
          <Link
            href="/search"
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-md font-semibold text-xs transition-colors shrink-0 text-center"
          >
            Run Test Search
          </Link>
        </div>
      )}

      {/* Stats Grid: 2 cols on mobile, 3 on tablet, 6 on desktop */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-4">
        {stats.map((stat, idx) => (
          <Link
            key={idx}
            href={stat.href}
            className="bg-white p-3 sm:p-4 rounded-xl border border-slate-200 shadow-2xs hover:border-blue-300 transition-all group flex flex-col justify-between min-w-0"
          >
            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <span className="text-[10px] sm:text-[11px] font-semibold text-slate-500 uppercase tracking-wider line-clamp-1 truncate mr-1">
                {stat.label}
              </span>
              <div className={`p-1.5 sm:p-2 rounded-lg ${stat.bgColor} shrink-0`}>
                <stat.icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${stat.color}`} />
              </div>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-slate-900 truncate">
              {isMetricsLoading ? "..." : stat.value}
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Launch Action Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 rounded-2xl p-4 sm:p-6 text-white shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1 text-left">
          <h2 className="text-lg sm:text-xl font-bold">Discover Leads in Any Indian City</h2>
          <p className="text-xs sm:text-sm text-blue-100 max-w-xl leading-relaxed">
            Target Salons, Restaurants, IT Companies, or Agencies in Mohali, Chandigarh, Delhi,
            Ludhiana, Bengaluru, or any Indian district with automated branch deduplication.
          </p>
        </div>
        <Link
          href="/search"
          className="w-full sm:w-auto px-5 py-2.5 sm:py-3 bg-white text-blue-700 font-bold rounded-xl text-xs sm:text-sm shadow hover:bg-blue-50 transition-colors flex items-center justify-center space-x-2 shrink-0"
        >
          <Search className="w-4 h-4" />
          <span>Launch Search</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Two Column Layout: Recent Jobs & Sourcing Quick Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6">
        {/* Recent Search Jobs */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 space-y-4 min-w-0">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center">
              <Briefcase className="w-4 h-4 text-blue-600 mr-2 shrink-0" />
              <span>Recent Discovery Jobs</span>
            </h3>
            <Link
              href="/jobs"
              className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1 shrink-0"
            >
              <span>View all jobs</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-100">
            {jobsData?.items && jobsData.items.length > 0 ? (
              jobsData.items.map((job) => (
                <div key={job.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-slate-900 truncate">
                      {job.category} in {job.resolved_city}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5 truncate">
                      Discovered {job.total_discovered} • Inserted {job.total_inserted} • Duplicates Flagged {job.total_duplicates_flagged}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
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
                      className="p-1 text-slate-400 hover:text-blue-600 rounded"
                      aria-label={`View details for ${job.category} in ${job.resolved_city}`}
                    >
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                No discovery jobs created yet. Click &quot;Launch Search&quot; to start one.
              </div>
            )}
          </div>
        </div>

        {/* System & Sourcing Provenance Info */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 space-y-4 min-w-0">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-3">
            System &amp; Data Provenance
          </h3>

          <div className="space-y-3 text-xs text-slate-600">
            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="font-semibold text-slate-800 mb-1">Geographic Boundary</div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Strictly validated for Republic of India. Non-Indian locations are rejected automatically.
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="font-semibold text-slate-800 mb-1">E.164 Phone Normalization</div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Normalized with Google&apos;s <code>libphonenumber</code> for India (+91 prefix, mobile vs landline).
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <div className="font-semibold text-slate-800 mb-1">Branch-Level Deduplication</div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Multi-stage RapidFuzz &amp; database matching preserves distinct branches (Phase 7 vs Phase 3B2).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
