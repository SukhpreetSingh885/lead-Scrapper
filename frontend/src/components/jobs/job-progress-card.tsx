"use client";

import React, { useState, useEffect } from "react";
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
  Trash2,
  Eraser,
  Loader2,
  X,
  MapPin,
  Info,
  Smartphone,
  Phone,
  Globe,
  MessageSquare,
  Table,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { DiscoveryJob } from "@/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useDeleteDiscoveryJob, useClearJobPreview } from "@/hooks/use-jobs";
import { SearchPreviewTable } from "@/components/search/search-preview-table";

interface JobProgressCardProps {
  job: DiscoveryJob;
  defaultExpandedPreview?: boolean;
}

export function JobProgressCard({ job, defaultExpandedPreview = false }: JobProgressCardProps) {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [isTableExpanded, setIsTableExpanded] = useState(defaultExpandedPreview);

  const deleteMutation = useDeleteDiscoveryJob();
  const clearMutation = useClearJobPreview();

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

  const hasUnsavedPreviewItems =
    (job.items && job.items.some((i) => !i.is_saved)) ||
    (job.total_discovered > 0 && job.total_inserted < job.total_discovered);

  // Close modals on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowDeleteModal(false);
        setShowClearModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 space-y-4 relative w-full min-w-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-bold text-sm sm:text-base text-slate-900 break-words">
              {job.category} in {job.resolved_city}, {job.resolved_state}
            </span>
            <Badge variant={statusVariant} className="uppercase text-[10px] shrink-0">
              {job.status.replace("_", " ")}
            </Badge>
          </div>
          <div className="text-xs text-slate-400 mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <span>Started {formatDate(job.started_at || job.created_at)}</span>
            <span>•</span>
            <span>Source: {job.source_code}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {isRunning && (
            <div className="flex items-center space-x-2 text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
              <RotateCw className="w-3.5 h-3.5 animate-spin shrink-0" />
              <span>Processing Discovery Pipeline...</span>
            </div>
          )}
        </div>
      </div>

      {/* Progress Counters Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 sm:gap-3">
        <div className="bg-slate-50 p-2.5 sm:p-3 rounded-lg border border-slate-100 min-w-0">
          <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider truncate">
            Discovered
          </div>
          <div className="text-base sm:text-lg font-bold text-slate-900 mt-0.5 truncate">
            {job.total_discovered} / {job.max_leads}
          </div>
        </div>

        <div className="bg-emerald-50/60 p-2.5 sm:p-3 rounded-lg border border-emerald-100 min-w-0">
          <div className="text-[10px] text-emerald-700 font-semibold uppercase tracking-wider truncate">
            Eligible
          </div>
          <div className="text-base sm:text-lg font-bold text-emerald-800 mt-0.5 truncate">
            {job.total_eligible}
          </div>
        </div>

        <div className="bg-teal-50/60 p-2.5 sm:p-3 rounded-lg border border-teal-100 min-w-0">
          <div className="text-[10px] text-teal-700 font-semibold uppercase tracking-wider truncate">
            Contact Qualified
          </div>
          <div className="text-base sm:text-lg font-bold text-teal-800 mt-0.5 truncate">
            {job.total_contact_qualified ?? (job.items ? job.items.filter((i) => Boolean(i.phone)).length : 0)}
          </div>
        </div>

        <div className="bg-blue-50/60 p-2.5 sm:p-3 rounded-lg border border-blue-100 min-w-0">
          <div className="text-[10px] text-blue-700 font-semibold uppercase tracking-wider truncate">
            Saved in CRM
          </div>
          <div className="text-base sm:text-lg font-bold text-blue-800 mt-0.5 truncate">
            {job.total_inserted}
          </div>
        </div>

        <div className="col-span-2 sm:col-span-1 bg-purple-50/60 p-2.5 sm:p-3 rounded-lg border border-purple-100 min-w-0">
          <div className="text-[10px] text-purple-700 font-semibold uppercase tracking-wider truncate">
            Already in CRM
          </div>
          <div className="text-base sm:text-lg font-bold text-purple-800 mt-0.5 truncate">
            {job.total_updated}
          </div>
        </div>
      </div>

      {/* Contact Channels & Enrichment Breakdown */}
      <div className="bg-slate-50/80 rounded-xl border border-slate-200/80 p-3 sm:p-3.5 space-y-2">
        <div className="text-[11px] font-semibold text-slate-700 uppercase tracking-wider flex items-center justify-between">
          <span>Contact Channels &amp; Enrichment Breakdown</span>
          <span className="text-slate-400 font-normal lowercase">phone extraction &amp; website crawl</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {/* Mobile Count */}
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 min-w-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-[10px] text-emerald-700 font-medium">
              <Smartphone className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span className="truncate">Mobile Leads</span>
            </div>
            <div className="text-sm sm:text-base font-bold text-emerald-800 mt-0.5">
              {job.total_mobile ?? 0}
            </div>
          </div>

          {/* Landline Count */}
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 min-w-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-[10px] text-blue-700 font-medium">
              <Phone className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              <span className="truncate">Landline</span>
            </div>
            <div className="text-sm sm:text-base font-bold text-blue-800 mt-0.5">
              {job.total_landline ?? 0}
            </div>
          </div>

          {/* WhatsApp Count */}
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 min-w-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-[10px] text-teal-700 font-medium">
              <MessageSquare className="w-3.5 h-3.5 text-teal-600 shrink-0" />
              <span className="truncate">WhatsApp</span>
            </div>
            <div className="text-sm sm:text-base font-bold text-teal-800 mt-0.5">
              {job.total_whatsapp ?? 0}
            </div>
          </div>

          {/* Missing Phones */}
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 min-w-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-[10px] text-amber-700 font-medium">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span className="truncate">Missing Phone</span>
            </div>
            <div className="text-sm sm:text-base font-bold text-amber-800 mt-0.5">
              {job.total_missing_phone ?? Math.max(0, job.total_discovered - (job.total_contact_qualified ?? 0))}
            </div>
          </div>

          {/* Website Enriched */}
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 min-w-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-[10px] text-indigo-700 font-medium">
              <Globe className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
              <span className="truncate">Enriched</span>
            </div>
            <div className="text-sm sm:text-base font-bold text-indigo-800 mt-0.5">
              {job.total_enriched ?? 0}
            </div>
          </div>

          {/* Enrichment Unavailable */}
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 min-w-0 shadow-2xs">
            <div className="flex items-center space-x-1 text-[10px] text-slate-500 font-medium">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="truncate">No Web / Unavail</span>
            </div>
            <div className="text-sm sm:text-base font-bold text-slate-700 mt-0.5">
              {job.total_enrichment_unavailable ?? 0}
            </div>
          </div>
        </div>
      </div>

      {/* Error message banner if failed */}
      {isFailed && job.error_message && (
        <div className="p-3 sm:p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div className="min-w-0 flex-1">
            <div className="font-semibold">Search Job Error</div>
            <div className="mt-0.5 break-words">{job.error_message}</div>
          </div>
        </div>
      )}

      {/* Per-City Multi-Location Discovery Breakdown */}
      {job.per_city_stats && job.per_city_stats.length > 0 && (
        <div className="bg-slate-50/80 rounded-xl border border-slate-200/80 p-3.5 space-y-2.5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <div className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              <span>Per-City Discovery Statistics ({job.per_city_stats.length} {job.per_city_stats.length === 1 ? "City" : "Cities"} Queried)</span>
            </div>
            <div className="text-[11px] text-slate-500">
              Total Overlapping Duplicates Removed: <span className="font-semibold text-slate-700">{job.per_city_stats.reduce((acc, s) => acc + s.duplicates_removed, 0)}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {job.per_city_stats.map((stat, idx) => (
              <div key={idx} className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-xs text-slate-900 flex items-center space-x-1">
                    <span>{stat.city}</span>
                    <span className="text-[10px] text-slate-400 font-normal">({stat.state})</span>
                  </div>
                  <span className="text-[10px] bg-blue-50 text-blue-700 font-medium px-1.5 py-0.5 rounded">
                    {Math.round(stat.radius_meters / 1000)} km radius
                  </span>
                </div>

                <div className="text-[10px] text-slate-400 font-mono">
                  Coordinates: {stat.latitude}, {stat.longitude}
                </div>

                <div className="grid grid-cols-3 gap-1 pt-1.5 border-t border-slate-100 text-center">
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold">Raw OSM</div>
                    <div className="text-xs font-bold text-slate-800 mt-0.5">{stat.raw_discovered}</div>
                  </div>
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-amber-600 font-semibold">Duplicates</div>
                    <div className="text-xs font-bold text-amber-700 mt-0.5">-{stat.duplicates_removed}</div>
                  </div>
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-emerald-600 font-semibold">Unique</div>
                    <div className="text-xs font-bold text-emerald-700 mt-0.5">+{stat.unique_contributed}</div>
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-100 flex items-center justify-between">
                  <span>Contact Qualified:</span>
                  <span className="font-semibold text-teal-700">{stat.contact_qualified}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[10px] text-slate-500 flex items-start space-x-1 pt-1">
            <Info className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" />
            <span>
              Each city executes an independent Overpass query around its municipal coordinates. Overlapping businesses across contiguous boundaries (e.g. Chandigarh, Mohali, Panchkula) are automatically deduplicated.
            </span>
          </div>
        </div>
      )}

      {/* Discovery Items Preview (Shown only when full table is collapsed) */}
      {!isTableExpanded && job.items && job.items.length > 0 && (
        <div className="border-t border-slate-100 pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-700">
              Discovered Results Preview ({job.items.length} items sampled)
            </span>
            <button
              type="button"
              onClick={() => setIsTableExpanded(true)}
              className="text-xs font-medium text-blue-600 hover:text-blue-800 flex items-center space-x-1"
            >
              <span>Expand Full Interactive Table ({job.total_eligible || job.total_discovered})</span>
              <ChevronDown className="w-3 h-3" />
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 border border-slate-200 rounded-lg text-xs">
            {job.items.map((item) => (
              <div key={item.id} className="p-2.5 flex items-start sm:items-center justify-between gap-2 hover:bg-slate-50">
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-slate-900 break-words line-clamp-1">{item.business_name}</div>
                  <div className="text-[11px] text-slate-500 truncate">{item.address || "No address"}</div>
                </div>
                <div className="text-right shrink-0">
                  {item.is_saved ? (
                    <Badge variant="success" className="text-[10px]">
                      Saved in CRM
                    </Badge>
                  ) : item.is_already_saved ? (
                    <Badge variant="outline" className="text-[10px] bg-slate-100 text-slate-700">
                      Already in CRM
                    </Badge>
                  ) : item.is_eligible_for_crm ? (
                    <Badge variant="outline" className="text-[10px] bg-emerald-50 text-emerald-700 border-emerald-300">
                      Preview (Unsaved)
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

      {/* Action link & Buttons Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100 text-xs">
        <div className="text-slate-500 text-xs">
          {job.total_inserted > 0 ? (
            <span className="text-emerald-700 font-medium">
              ✓ {job.total_inserted} lead{job.total_inserted > 1 ? "s" : ""} saved in CRM database
            </span>
          ) : (
            <span className="text-amber-700 font-medium">
              ⓘ {job.total_eligible} preview lead{job.total_eligible === 1 ? "" : "s"} in Discovery Preview (not yet saved to CRM)
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle Full Preview Table Button */}
          <button
            type="button"
            onClick={() => setIsTableExpanded((prev) => !prev)}
            className={`px-3 py-1.5 border rounded-lg text-xs font-semibold inline-flex items-center space-x-1.5 transition-colors touch-manipulation ${
              isTableExpanded
                ? "bg-blue-600 text-white border-blue-600 hover:bg-blue-700 shadow-2xs"
                : "bg-white text-blue-700 hover:bg-blue-50 border-blue-200"
            }`}
          >
            <Table className="w-3.5 h-3.5 shrink-0" />
            <span>
              {isTableExpanded
                ? "Hide Preview Leads"
                : `View Preview Leads (${job.total_eligible || job.total_discovered})`}
            </span>
            {isTableExpanded ? (
              <ChevronUp className="w-3.5 h-3.5 shrink-0" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 shrink-0" />
            )}
          </button>

          {/* Clear Preview Button */}
          {hasUnsavedPreviewItems && (
            <button
              type="button"
              onClick={() => setShowClearModal(true)}
              disabled={clearMutation.isPending || deleteMutation.isPending}
              className="px-2.5 py-1.5 text-slate-700 hover:text-amber-800 hover:bg-amber-50 border border-slate-200 hover:border-amber-300 rounded-lg text-xs font-medium inline-flex items-center space-x-1.5 transition-colors disabled:opacity-50 touch-manipulation"
              title="Remove unsaved temporary preview records without deleting the search job"
            >
              <Eraser className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>Clear Preview</span>
            </button>
          )}

          {/* Delete Job Button */}
          <button
            type="button"
            onClick={() => setShowDeleteModal(true)}
            disabled={deleteMutation.isPending || clearMutation.isPending}
            className="px-2.5 py-1.5 text-rose-700 hover:text-rose-900 hover:bg-rose-50 border border-rose-200 hover:border-rose-300 rounded-lg text-xs font-medium inline-flex items-center space-x-1.5 transition-colors disabled:opacity-50 touch-manipulation"
            title="Permanently delete this search job and its preview records"
          >
            {deleteMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-600 shrink-0" />
            ) : (
              <Trash2 className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            )}
            <span>Delete Job</span>
          </button>

          {/* View CRM leads link */}
          {job.total_inserted > 0 ? (
            <Link
              href={`/leads?job_id=${encodeURIComponent(job.id)}&category=${encodeURIComponent(job.category)}&city=${encodeURIComponent(job.resolved_city)}`}
              className="px-2.5 py-1.5 text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center space-x-1 bg-blue-50 border border-blue-200 rounded-lg touch-manipulation"
            >
              <span>View {job.total_inserted} Saved CRM Leads</span>
              <ExternalLink className="w-3.5 h-3.5 shrink-0" />
            </Link>
          ) : (
            <Link
              href={`/leads?category=${encodeURIComponent(job.category)}&city=${encodeURIComponent(job.resolved_city)}`}
              className="px-2.5 py-1.5 text-slate-600 hover:text-blue-700 font-medium inline-flex items-center space-x-1 border border-slate-200 rounded-lg hover:bg-slate-50 touch-manipulation"
              title="View all existing saved CRM leads in this category and city"
            >
              <span>View All Saved {job.category} in CRM</span>
              <ExternalLink className="w-3.5 h-3.5 shrink-0" />
            </Link>
          )}
        </div>
      </div>

      {/* Expanded Interactive Full Discovered Leads Table */}
      {isTableExpanded && (
        <div className="pt-2 animate-in fade-in duration-200">
          <SearchPreviewTable jobId={job.id} />
        </div>
      )}

      {/* Delete Job Confirmation Modal */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
          onClick={() => setShowDeleteModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="bg-white rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start space-x-3">
              <div className="p-2.5 rounded-full bg-rose-50 text-rose-600 shrink-0">
                <Trash2 className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-base font-bold text-slate-900">Delete Search Job?</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Are you sure you want to delete the search job for{" "}
                  <strong className="text-slate-800 break-words">{job.category} in {job.resolved_city}</strong>?
                </p>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-1.5 text-slate-600">
              <div className="flex items-center space-x-2 text-rose-700 font-medium">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>Temporary preview records for this job will be permanently removed.</span>
              </div>
              <div className="flex items-center space-x-2 text-emerald-700 font-medium">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Permanent CRM leads already saved in your database will NOT be deleted.</span>
              </div>
              {isRunning && (
                <div className="flex items-center space-x-2 text-amber-700 font-medium pt-1 border-t border-slate-200">
                  <RotateCw className="w-4 h-4 shrink-0 animate-spin" />
                  <span>This job is currently active; background processing will be safely cancelled first.</span>
                </div>
              )}
            </div>

            {deleteMutation.isError && (
              <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 p-2.5 rounded-lg break-words">
                {(deleteMutation.error as any)?.message || "Failed to delete job. Please try again."}
              </div>
            )}

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition touch-manipulation"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  deleteMutation.mutate(job.id, {
                    onSuccess: () => {
                      setShowDeleteModal(false);
                    },
                  });
                }}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50 shadow-xs touch-manipulation"
              >
                {deleteMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting Job...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Confirm Delete Job</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear Preview Confirmation Modal */}
      {showClearModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
          onClick={() => setShowClearModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="bg-white rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start space-x-3">
              <div className="p-2.5 rounded-full bg-amber-50 text-amber-600 shrink-0">
                <Eraser className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-base font-bold text-slate-900">Clear Unsaved Preview Leads?</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Remove unsaved discovery preview results for{" "}
                  <strong className="text-slate-800 break-words">{job.category} in {job.resolved_city}</strong>?
                </p>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-1.5 text-slate-600">
              <div className="flex items-center space-x-2 text-slate-700">
                <Clock className="w-4 h-4 text-slate-500 shrink-0" />
                <span>The search job entry and its historical parameters will be preserved.</span>
              </div>
              <div className="flex items-center space-x-2 text-emerald-700 font-medium">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Permanent CRM leads already saved in your database will NOT be deleted.</span>
              </div>
            </div>

            {clearMutation.isError && (
              <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 p-2.5 rounded-lg break-words">
                {(clearMutation.error as any)?.message || "Failed to clear preview. Please try again."}
              </div>
            )}

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowClearModal(false)}
                disabled={clearMutation.isPending}
                className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition touch-manipulation"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  clearMutation.mutate(job.id, {
                    onSuccess: () => {
                      setShowClearModal(false);
                    },
                  });
                }}
                disabled={clearMutation.isPending}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50 shadow-xs touch-manipulation"
              >
                {clearMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Clearing...</span>
                  </>
                ) : (
                  <>
                    <Eraser className="w-3.5 h-3.5" />
                    <span>Confirm Clear Preview</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
