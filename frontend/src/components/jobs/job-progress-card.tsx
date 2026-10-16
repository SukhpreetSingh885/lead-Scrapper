"use client";

import React from "react";
import Link from "next/link";
import {
  Briefcase,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RotateCw,
  Database,
  Users,
  CopyX,
  ExternalLink,
} from "lucide-react";
import { DiscoveryJob } from "@/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface JobProgressCardProps {
  job: DiscoveryJob;
}

export function JobProgressCard({ job }: JobProgressCardProps) {
  const isRunning = ["pending", "queued", "running"].includes(job.status);
  const isFailed = job.status === "failed";
  const isCompleted = job.status === "completed" || job.status === "partially_completed";

  const statusVariant = {
    pending: "secondary" as const,
    queued: "secondary" as const,
    running: "warning" as const,
    completed: "success" as const,
    partially_completed: "warning" as const,
    failed: "destructive" as const,
    cancelled: "secondary" as const,
  }[job.status] || "secondary";

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-base text-slate-900">
              {job.category} in {job.resolved_city}, {job.resolved_state}
            </span>
            <Badge variant={statusVariant} className="uppercase text-[10px]">
              {job.status.replace("_", " ")}
            </Badge>
          </div>
          <div className="text-xs text-slate-400 mt-0.5 flex items-center space-x-2">
            <span>Started {formatDate(job.started_at || job.created_at)}</span>
            <span>•</span>
            <span>Source: {job.source_code}</span>
          </div>
        </div>

        {isRunning && (
          <div className="flex items-center space-x-2 text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
            <RotateCw className="w-3.5 h-3.5 animate-spin" />
            <span>Processing Discovery Pipeline...</span>
          </div>
        )}
      </div>

      {/* Progress Counters Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
          <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
            Discovered
          </div>
          <div className="text-lg font-bold text-slate-900 mt-0.5">
            {job.total_discovered} / {job.max_leads}
          </div>
        </div>

        <div className="bg-emerald-50/60 p-3 rounded-lg border border-emerald-100">
          <div className="text-[10px] text-emerald-700 font-semibold uppercase tracking-wider">
            Eligible
          </div>
          <div className="text-lg font-bold text-emerald-800 mt-0.5">
            {job.total_eligible}
          </div>
        </div>

        <div className="bg-blue-50/60 p-3 rounded-lg border border-blue-100">
          <div className="text-[10px] text-blue-700 font-semibold uppercase tracking-wider">
            New Inserted
          </div>
          <div className="text-lg font-bold text-blue-800 mt-0.5">
            {job.total_inserted}
          </div>
        </div>

        <div className="bg-purple-50/60 p-3 rounded-lg border border-purple-100">
          <div className="text-[10px] text-purple-700 font-semibold uppercase tracking-wider">
            Updated Dups
          </div>
          <div className="text-lg font-bold text-purple-800 mt-0.5">
            {job.total_updated}
          </div>
        </div>

        <div className="bg-amber-50/60 p-3 rounded-lg border border-amber-100">
          <div className="text-[10px] text-amber-700 font-semibold uppercase tracking-wider">
            Review Flagged
          </div>
          <div className="text-lg font-bold text-amber-800 mt-0.5">
            {job.total_duplicates_flagged}
          </div>
        </div>
      </div>

      {/* Error message banner if failed */}
      {isFailed && job.error_message && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Search Job Error</div>
            <div className="mt-0.5">{job.error_message}</div>
          </div>
        </div>
      )}

      {/* Discovery Items Preview (e.g. temporary Google Places preview or CRM items) */}
      {job.items && job.items.length > 0 && (
        <div className="border-t border-slate-100 pt-3">
          <div className="text-xs font-semibold text-slate-700 mb-2">
            Discovered Results Preview ({job.items.length} items)
          </div>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 border border-slate-200 rounded-lg text-xs">
            {job.items.map((item) => (
              <div key={item.id} className="p-2.5 flex items-center justify-between hover:bg-slate-50">
                <div>
                  <div className="font-medium text-slate-900">{item.business_name}</div>
                  <div className="text-[11px] text-slate-500">{item.address || "No address"}</div>
                </div>
                <div className="text-right">
                  {item.is_eligible_for_crm ? (
                    <Badge variant="success" className="text-[10px]">
                      CRM Saved
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-[10px]" title={item.rejection_reason || ""}>
                      Discovery Preview Only
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action link */}
      <div className="flex items-center justify-end space-x-3 pt-2 text-xs">
        <Link
          href={`/leads?city=${encodeURIComponent(job.resolved_city)}`}
          className="text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center space-x-1"
        >
          <span>View Saved Leads in {job.resolved_city}</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}

