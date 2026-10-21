"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Clock,
  Phone,
  Smartphone,
  Mail,
  Globe,
  MapPin,
  Save,
  AlertCircle,
  ExternalLink,
  Info,
  Loader2,
  X,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Filter,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { DiscoveryPreviewItem } from "@/types";
import {
  useDiscoveryJobPreview,
  useDiscoveryJob,
  useSaveSelectedLeads,
} from "@/hooks/use-jobs";

interface SearchPreviewTableProps {
  jobId: string;
}

type FilterType = "all" | "mobile" | "landline" | "whatsapp" | "has_phone" | "unsaved";

export function SearchPreviewTable({ jobId }: SearchPreviewTableProps) {
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(50);
  const [filterType, setFilterType] = useState<FilterType>("all");

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activeItemDetails, setActiveItemDetails] = useState<DiscoveryPreviewItem | null>(null);
  const [saveFeedback, setSaveFeedback] = useState<{
    saved_count: number;
    already_existing_count: number;
    message: string;
  } | null>(null);

  // Filters computed from state
  const filters = useMemo(() => {
    switch (filterType) {
      case "mobile":
        return { must_have_mobile: true };
      case "landline":
        return { must_have_landline: true };
      case "whatsapp":
        return { must_have_whatsapp: true };
      case "has_phone":
        return { must_have_phone: true };
      case "unsaved":
        return { exclude_already_saved: true };
      default:
        return undefined;
    }
  }, [filterType]);

  const { data: job } = useDiscoveryJob(jobId);
  const {
    data: previewData,
    isLoading,
    isFetching,
    refetch,
  } = useDiscoveryJobPreview(jobId, page, pageSize, filters);

  const saveMutation = useSaveSelectedLeads();

  const items = previewData?.items || [];
  const total = previewData?.total || 0;
  const totalPages = previewData?.total_pages || Math.max(1, Math.ceil(total / pageSize));

  const eligibleItemsOnPage = items.filter(
    (item) => item.is_eligible_for_crm && !item.is_saved && !item.is_already_saved
  );

  // Close modal on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setActiveItemDetails(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Handle filter change
  const handleFilterChange = (newFilter: FilterType) => {
    setFilterType(newFilter);
    setPage(1);
  };

  // Handle page size change
  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  };

  // Toggle selection for a single item
  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  // Select all eligible unsaved leads on current page
  const selectPageEligible = () => {
    const pageIds = eligibleItemsOnPage.map((item) => item.id);
    setSelectedIds((prev) => Array.from(new Set([...prev, ...pageIds])));
  };

  // Clear all selections
  const clearSelection = () => {
    setSelectedIds([]);
  };

  // Save selected leads handler
  const handleSaveSelected = () => {
    if (selectedIds.length === 0) return;
    setSaveFeedback(null);

    saveMutation.mutate(
      {
        job_id: jobId,
        item_ids: selectedIds,
        save_all_eligible: false,
      },
      {
        onSuccess: (res) => {
          setSaveFeedback({
            saved_count: res.saved_count,
            already_existing_count: res.already_existing_count,
            message: res.message,
          });
          setSelectedIds([]);
          refetch();
        },
      }
    );
  };

  // Save all eligible leads handler
  const handleSaveAllEligible = () => {
    setSaveFeedback(null);

    saveMutation.mutate(
      {
        job_id: jobId,
        save_all_eligible: true,
      },
      {
        onSuccess: (res) => {
          setSaveFeedback({
            saved_count: res.saved_count,
            already_existing_count: res.already_existing_count,
            message: res.message,
          });
          setSelectedIds([]);
          refetch();
        },
      }
    );
  };

  const startRecord = total > 0 ? (page - 1) * pageSize + 1 : 0;
  const endRecord = total > 0 ? Math.min(page * pageSize, total) : 0;

  if (isLoading && items.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
        <div className="text-sm font-semibold text-slate-700">Loading Discovered Leads Preview...</div>
        <div className="text-xs text-slate-400">Querying real business records from OpenStreetMap Overpass</div>
      </div>
    );
  }

  if (total === 0 && filterType === "all") {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center space-y-2">
        <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
        <div className="text-sm font-semibold text-slate-700">No Discovered Leads Found</div>
        <div className="text-xs text-slate-500 max-w-md mx-auto">
          The background discovery job is still searching or no records were returned in this radius.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden w-full min-w-0">
      {/* Top Banner & Action Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-200 bg-slate-50/50 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                Search Discovery Preview ({total} Discovered Leads)
              </h3>
              <Badge variant="outline" className="text-[10px] text-amber-700 border-amber-300 bg-amber-50 shrink-0">
                <Clock className="w-3 h-3 mr-1 shrink-0" />
                Temporary Preview (24h)
              </Badge>
              {isFetching && !isLoading && (
                <span className="text-[11px] text-blue-600 flex items-center space-x-1 shrink-0">
                  <Loader2 className="w-3 h-3 animate-spin shrink-0" />
                  <span>Updating...</span>
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Review live discovered businesses below. Select and click &quot;Save Selected Leads&quot; to permanently store in CRM.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-2">
            {selectedIds.length > 0 ? (
              <button
                type="button"
                onClick={clearSelection}
                className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg text-xs font-medium text-slate-700 transition touch-manipulation"
              >
                Clear ({selectedIds.length})
              </button>
            ) : (
              <button
                type="button"
                onClick={selectPageEligible}
                disabled={eligibleItemsOnPage.length === 0}
                className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg text-xs font-medium text-slate-700 transition disabled:opacity-50 touch-manipulation"
              >
                Select Page ({eligibleItemsOnPage.length})
              </button>
            )}

            <button
              type="button"
              onClick={handleSaveSelected}
              disabled={selectedIds.length === 0 || saveMutation.isPending}
              className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center space-x-1.5 disabled:opacity-50 touch-manipulation"
            >
              {saveMutation.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5 shrink-0" />
                  <span>Save Selected ({selectedIds.length})</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleSaveAllEligible}
              disabled={(job?.total_eligible ?? total) === 0 || saveMutation.isPending}
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center space-x-1.5 disabled:opacity-50 touch-manipulation"
              title="Save all eligible leads from this search directly into CRM database"
            >
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>Save All Eligible ({job?.total_eligible ?? total})</span>
            </button>
          </div>
        </div>

        {/* Filter Toggle Chips */}
        <div className="pt-2 border-t border-slate-200/80 flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider mr-1 flex items-center">
            <Filter className="w-3 h-3 mr-1 text-slate-400 shrink-0" />
            Filter:
          </span>

          <button
            type="button"
            onClick={() => handleFilterChange("all")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition touch-manipulation flex items-center space-x-1.5 ${
              filterType === "all"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
            }`}
          >
            <span>All</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${filterType === "all" ? "bg-slate-700 text-slate-200" : "bg-slate-100 text-slate-600"}`}>
              {job?.total_discovered ?? total}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleFilterChange("mobile")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition touch-manipulation flex items-center space-x-1.5 ${
              filterType === "mobile"
                ? "bg-emerald-700 text-white shadow-xs"
                : "bg-white text-emerald-800 hover:bg-emerald-50 border border-emerald-200"
            }`}
          >
            <Smartphone className="w-3 h-3 shrink-0" />
            <span>Mobile Numbers</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${filterType === "mobile" ? "bg-emerald-800 text-emerald-100" : "bg-emerald-100 text-emerald-800"}`}>
              {job?.total_mobile ?? 0}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleFilterChange("landline")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition touch-manipulation flex items-center space-x-1.5 ${
              filterType === "landline"
                ? "bg-blue-700 text-white shadow-xs"
                : "bg-white text-blue-800 hover:bg-blue-50 border border-blue-200"
            }`}
          >
            <Phone className="w-3 h-3 shrink-0" />
            <span>Landline</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${filterType === "landline" ? "bg-blue-800 text-blue-100" : "bg-blue-100 text-blue-800"}`}>
              {job?.total_landline ?? 0}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleFilterChange("whatsapp")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition touch-manipulation flex items-center space-x-1.5 ${
              filterType === "whatsapp"
                ? "bg-teal-700 text-white shadow-xs"
                : "bg-white text-teal-800 hover:bg-teal-50 border border-teal-200"
            }`}
          >
            <MessageSquare className="w-3 h-3 shrink-0" />
            <span>WhatsApp</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${filterType === "whatsapp" ? "bg-teal-800 text-teal-100" : "bg-teal-100 text-teal-800"}`}>
              {job?.total_whatsapp ?? 0}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleFilterChange("has_phone")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition touch-manipulation flex items-center space-x-1.5 ${
              filterType === "has_phone"
                ? "bg-indigo-700 text-white shadow-xs"
                : "bg-white text-indigo-800 hover:bg-indigo-50 border border-indigo-200"
            }`}
          >
            <span>Any Contact Phone</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${filterType === "has_phone" ? "bg-indigo-800 text-indigo-100" : "bg-indigo-100 text-indigo-800"}`}>
              {job?.total_contact_qualified ?? 0}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleFilterChange("unsaved")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition touch-manipulation flex items-center space-x-1.5 ${
              filterType === "unsaved"
                ? "bg-amber-700 text-white shadow-xs"
                : "bg-white text-amber-800 hover:bg-amber-50 border border-amber-200"
            }`}
          >
            <span>Unsaved Only</span>
          </button>
        </div>

        {/* Success / Feedback Banner */}
        {saveFeedback && (
          <div className="p-3 sm:p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-start sm:items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5 sm:mt-0" />
              <span className="leading-relaxed">
                <strong>{saveFeedback.message}</strong> Newly saved: {saveFeedback.saved_count}, Already in DB: {saveFeedback.already_existing_count}.
              </span>
            </div>
            <Link
              href="/leads"
              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium text-[11px] inline-flex items-center space-x-1 shrink-0 self-start sm:self-center"
            >
              <span>View in Saved Leads</span>
              <ExternalLink className="w-3 h-3 shrink-0" />
            </Link>
          </div>
        )}
      </div>

      {/* When no items match current filter */}
      {items.length === 0 ? (
        <div className="p-8 text-center space-y-2 bg-slate-50/40">
          <AlertCircle className="w-7 h-7 text-slate-400 mx-auto" />
          <div className="text-sm font-semibold text-slate-700">No leads match the selected filter</div>
          <p className="text-xs text-slate-500">
            Try switching to &quot;All&quot; or clearing active filters to see all {total} discovered leads.
          </p>
          <button
            type="button"
            onClick={() => handleFilterChange("all")}
            className="mt-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium"
          >
            Reset Filter to All
          </button>
        </div>
      ) : (
        <>
          {/* MOBILE CARD VIEW (< 640px) */}
          <div className="sm:hidden divide-y divide-slate-100">
            {items.map((item) => {
              const isSelected = selectedIds.includes(item.id);
              const isAlreadySaved = item.is_saved || item.is_already_saved;
              const isLandline = Boolean(item.phone && item.phone !== item.mobile);

              return (
                <div
                  key={item.id}
                  className={`p-3.5 space-y-2.5 transition-colors ${isSelected ? "bg-blue-50/40" : "bg-white"}`}
                >
                  {/* Top row: Checkbox, Name, Status */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start space-x-2.5 min-w-0 flex-1">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        disabled={isAlreadySaved || !item.is_eligible_for_crm}
                        onChange={() => toggleSelect(item.id)}
                        className="mt-1 rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0 disabled:opacity-40"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-slate-900 text-sm break-words leading-tight">
                          {item.business_name}
                        </div>
                        <div className="inline-block mt-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[10px]">
                          {item.category || "Commercial"}
                        </div>
                      </div>
                    </div>

                    <div className="shrink-0 text-right">
                      {item.is_saved ? (
                        <Badge variant="success" className="text-[9px]">
                          Saved
                        </Badge>
                      ) : item.is_already_saved ? (
                        <Badge variant="outline" className="text-[9px] bg-slate-100 text-slate-700 border-slate-300">
                          In CRM
                        </Badge>
                      ) : item.is_eligible_for_crm ? (
                        <Badge variant="outline" className="text-[9px] bg-emerald-50 text-emerald-700 border-emerald-300">
                          New Lead
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[9px]">
                          Preview
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Address */}
                  <div className="text-xs text-slate-600 pl-6 space-y-0.5">
                    <div className="line-clamp-2">{item.address || `${item.city || "India"}`}</div>
                    <div className="text-[11px] text-slate-400 flex items-center space-x-1">
                      <MapPin className="w-3 h-3 shrink-0" />
                      <span>{item.city}, {item.state}</span>
                    </div>
                  </div>

                  {/* Contacts info & Actions */}
                  <div className="pl-6 pt-1 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 text-xs">
                    <div className="space-y-1">
                      {item.mobile && (
                        <div className="flex items-center space-x-1.5 text-slate-800 text-xs font-mono">
                          <Smartphone className="w-3 h-3 text-emerald-600 shrink-0" />
                          <span className="font-semibold text-emerald-900">{item.mobile}</span>
                          <span className="text-[9px] bg-emerald-50 text-emerald-700 px-1 py-0.2 rounded font-sans">Mobile</span>
                        </div>
                      )}
                      {isLandline && (
                        <div className="flex items-center space-x-1.5 text-slate-800 text-xs font-mono">
                          <Phone className="w-3 h-3 text-blue-600 shrink-0" />
                          <span className="text-blue-900">{item.phone}</span>
                          <span className="text-[9px] bg-blue-50 text-blue-700 px-1 py-0.2 rounded font-sans">Landline</span>
                        </div>
                      )}
                      {item.whatsapp && (
                        <div className="flex items-center space-x-1 text-teal-700 text-[10px] font-medium">
                          <MessageSquare className="w-3 h-3 text-teal-600 shrink-0" />
                          <span>WhatsApp: {item.whatsapp}</span>
                        </div>
                      )}
                      {!item.mobile && !item.phone && !item.whatsapp && (
                        <span className="text-[11px] text-slate-400">No phone number tagged</span>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => setActiveItemDetails(item)}
                        className="px-2.5 py-1 text-xs text-blue-600 hover:text-blue-800 font-medium hover:bg-blue-50 rounded transition touch-manipulation"
                      >
                        Details
                      </button>
                      {!isAlreadySaved && item.is_eligible_for_crm && (
                        <button
                          type="button"
                          onClick={() => {
                            saveMutation.mutate(
                              { job_id: jobId, item_ids: [item.id] },
                              {
                                onSuccess: (res) => {
                                  setSaveFeedback({
                                    saved_count: res.saved_count,
                                    already_existing_count: res.already_existing_count,
                                    message: res.message,
                                  });
                                  refetch();
                                },
                              }
                            );
                          }}
                          className="px-2.5 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition touch-manipulation"
                        >
                          Save
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* DESKTOP & TABLET TABLE VIEW (>= 640px) */}
          <div className="hidden sm:block overflow-x-auto min-w-0">
            <table className="w-full text-left text-xs border-collapse min-w-[750px]">
              <thead>
                <tr className="bg-slate-100/75 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="p-3 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={
                        eligibleItemsOnPage.length > 0 &&
                        eligibleItemsOnPage.every((item) => selectedIds.includes(item.id))
                      }
                      onChange={(e) => {
                        if (e.target.checked) selectPageEligible();
                        else clearSelection();
                      }}
                      className="rounded text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                    />
                  </th>
                  <th className="p-3">Business Name &amp; Category</th>
                  <th className="p-3">Location &amp; Address</th>
                  <th className="p-3">Contact Channels</th>
                  <th className="p-3">Online Presence</th>
                  <th className="p-3 text-center">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => {
                  const isSelected = selectedIds.includes(item.id);
                  const isAlreadySaved = item.is_saved || item.is_already_saved;
                  const isLandline = Boolean(item.phone && item.phone !== item.mobile);

                  return (
                    <tr
                      key={item.id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        isSelected ? "bg-blue-50/40" : ""
                      }`}
                    >
                      <td className="p-3 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          disabled={isAlreadySaved || !item.is_eligible_for_crm}
                          onChange={() => toggleSelect(item.id)}
                          className="rounded text-blue-600 focus:ring-blue-500 w-3.5 h-3.5 disabled:opacity-40"
                        />
                      </td>

                      <td className="p-3 max-w-[220px]">
                        <div className="font-semibold text-slate-900 text-xs truncate">{item.business_name}</div>
                        <div className="inline-block mt-0.5 px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[10px]">
                          {item.category || "Commercial"}
                        </div>
                      </td>

                      <td className="p-3 text-slate-600 max-w-xs">
                        <div className="truncate text-xs font-medium text-slate-800">
                          {item.address || `${item.city || "India"}`}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5 flex items-center space-x-1">
                          <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>{item.city}, {item.state}</span>
                        </div>
                      </td>

                      <td className="p-3 min-w-[190px]">
                        <div className="space-y-1">
                          {item.mobile && (
                            <div className="flex items-center space-x-1.5 text-slate-800 text-xs">
                              <Smartphone className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                              <span className="font-mono font-medium text-emerald-950">{item.mobile}</span>
                              <span className="text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-1 py-0.2 rounded font-sans">
                                Mobile
                              </span>
                            </div>
                          )}

                          {isLandline && (
                            <div className="flex items-center space-x-1.5 text-slate-800 text-xs">
                              <Phone className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                              <span className="font-mono text-blue-950">{item.phone}</span>
                              <span className="text-[9px] bg-blue-50 text-blue-700 border border-blue-200 px-1 py-0.2 rounded font-sans">
                                Landline
                              </span>
                            </div>
                          )}

                          {item.whatsapp && (
                            <div className="flex items-center space-x-1 text-teal-700 text-[10px] font-medium">
                              <MessageSquare className="w-3 h-3 text-teal-600 shrink-0" />
                              <span>WhatsApp Active ({item.whatsapp})</span>
                            </div>
                          )}

                          {!item.mobile && !item.phone && !item.whatsapp && (
                            <span className="text-[11px] text-slate-400">No phone tagged</span>
                          )}
                        </div>
                      </td>

                      <td className="p-3">
                        <div className="space-y-1">
                          {item.website ? (
                            <a
                              href={item.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-xs flex items-center space-x-1 max-w-[150px] truncate"
                            >
                              <Globe className="w-3 h-3 shrink-0" />
                              <span className="truncate">{item.website.replace(/^https?:\/\//, "")}</span>
                            </a>
                          ) : (
                            <span className="text-[11px] text-slate-400">No website</span>
                          )}

                          {item.email ? (
                            <div className="flex items-center space-x-1 text-slate-600 text-[11px]">
                              <Mail className="w-3 h-3 text-slate-400 shrink-0" />
                              <span className="truncate max-w-[130px]">{item.email}</span>
                            </div>
                          ) : null}
                        </div>
                      </td>

                      <td className="p-3 text-center">
                        {item.is_saved ? (
                          <Badge variant="success" className="text-[10px]">
                            Saved in CRM
                          </Badge>
                        ) : item.is_already_saved ? (
                          <Badge variant="outline" className="text-[10px] bg-slate-100 text-slate-700 border-slate-300">
                            Already in CRM
                          </Badge>
                        ) : item.is_eligible_for_crm ? (
                          <Badge variant="outline" className="text-[10px] bg-emerald-50 text-emerald-700 border-emerald-300">
                            New Lead
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-[10px]" title={item.rejection_reason || ""}>
                            Preview Only
                          </Badge>
                        )}
                      </td>

                      <td className="p-3 text-right space-x-1">
                        <button
                          type="button"
                          onClick={() => setActiveItemDetails(item)}
                          className="px-2.5 py-1 text-xs text-blue-600 hover:text-blue-800 font-medium hover:bg-blue-50 rounded transition touch-manipulation"
                        >
                          Details
                        </button>
                        {!isAlreadySaved && item.is_eligible_for_crm && (
                          <button
                            type="button"
                            onClick={() => {
                              saveMutation.mutate(
                                { job_id: jobId, item_ids: [item.id] },
                                {
                                  onSuccess: (res) => {
                                    setSaveFeedback({
                                      saved_count: res.saved_count,
                                      already_existing_count: res.already_existing_count,
                                      message: res.message,
                                    });
                                    refetch();
                                  },
                                }
                              );
                            }}
                            className="px-2.5 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition touch-manipulation"
                          >
                            Save
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* PAGINATION CONTROLS BAR */}
          <div className="p-3 sm:p-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-3 text-slate-600">
              <span>
                Showing <strong className="text-slate-900">{startRecord}</strong> to{" "}
                <strong className="text-slate-900">{endRecord}</strong> of{" "}
                <strong className="text-slate-900">{total}</strong> leads
              </span>

              <div className="flex items-center space-x-1.5 pl-2 sm:border-l border-slate-300">
                <span className="text-slate-500">Rows per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  className="bg-white border border-slate-300 rounded px-2 py-1 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={250}>250</option>
                  <option value={500}>500</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-1 sm:space-x-1.5">
              <span className="text-slate-500 mr-2">
                Page <strong className="text-slate-800">{page}</strong> of{" "}
                <strong className="text-slate-800">{totalPages}</strong>
              </span>

              <button
                type="button"
                onClick={() => setPage(1)}
                disabled={page <= 1 || isFetching}
                className="p-1.5 sm:px-2.5 sm:py-1 border border-slate-300 rounded-lg hover:bg-white disabled:opacity-40 transition touch-manipulation text-slate-700 font-medium"
                title="First Page"
              >
                <ChevronsLeft className="w-3.5 h-3.5" />
              </button>

              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || isFetching}
                className="px-2.5 py-1 border border-slate-300 rounded-lg hover:bg-white disabled:opacity-40 transition touch-manipulation text-slate-700 font-medium flex items-center space-x-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Previous</span>
              </button>

              <button
                type="button"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || isFetching}
                className="px-2.5 py-1 border border-slate-300 rounded-lg hover:bg-white disabled:opacity-40 transition touch-manipulation text-slate-700 font-medium flex items-center space-x-1"
              >
                <span className="hidden sm:inline">Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>

              <button
                type="button"
                onClick={() => setPage(totalPages)}
                disabled={page >= totalPages || isFetching}
                className="p-1.5 sm:px-2.5 sm:py-1 border border-slate-300 rounded-lg hover:bg-white disabled:opacity-40 transition touch-manipulation text-slate-700 font-medium"
                title="Last Page"
              >
                <ChevronsRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </>
      )}

      {/* Details Popup Modal */}
      {activeItemDetails && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150"
          onClick={() => setActiveItemDetails(null)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-5 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b border-slate-100 pb-3 gap-2">
              <div className="min-w-0 flex-1">
                <h4 className="font-bold text-base text-slate-900 break-words">{activeItemDetails.business_name}</h4>
                <div className="text-xs text-slate-500 truncate">{activeItemDetails.category || "Commercial Enterprise"}</div>
              </div>
              <button
                type="button"
                onClick={() => setActiveItemDetails(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 shrink-0 touch-manipulation"
                aria-label="Close details"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-semibold text-slate-700 block mb-0.5">Full Address:</span>
                <span className="text-slate-600 break-words">
                  {activeItemDetails.address || "Address not explicitly tagged in source."}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div>
                  <span className="font-semibold text-slate-700 block">City / State:</span>
                  <span className="text-slate-600">{activeItemDetails.city}, {activeItemDetails.state}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-700 block">Data Source:</span>
                  <span className="text-slate-600 uppercase font-mono">{activeItemDetails.source || activeItemDetails.source_code || "overpass"}</span>
                </div>
              </div>

              <div>
                <span className="font-semibold text-slate-700 block mb-1">Classified Contact Channels:</span>
                <div className="space-y-1 bg-slate-50 p-3 rounded-lg border border-slate-100 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span>Mobile:</span>
                    <span className="font-semibold text-emerald-800">{activeItemDetails.mobile || "Not Available"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Landline:</span>
                    <span className="font-semibold text-blue-800">{activeItemDetails.phone || "Not Available"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>WhatsApp:</span>
                    <span className="font-semibold text-teal-800">{activeItemDetails.whatsapp || "Not Available"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Email:</span>
                    <span className="break-all">{activeItemDetails.email || "Not Available"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Website:</span>
                    <span className="break-all">{activeItemDetails.website || "Not Available"}</span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-blue-50/70 border border-blue-100 rounded-lg text-blue-900 leading-relaxed text-[11px]">
                <div className="font-semibold mb-0.5 flex items-center">
                  <Info className="w-3.5 h-3.5 mr-1 shrink-0" />
                  <span>Compliance &amp; Licensing Notice</span>
                </div>
                Sourced legally from OpenStreetMap contributors under Open Database License (ODbL 1.0). Preview items are stored temporarily for 24 hours. Saving adds this verified business to your CRM organization.
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActiveItemDetails(null)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 touch-manipulation"
              >
                Close
              </button>
              {!activeItemDetails.is_saved && !activeItemDetails.is_already_saved && activeItemDetails.is_eligible_for_crm && (
                <button
                  type="button"
                  onClick={() => {
                    saveMutation.mutate(
                      {
                        job_id: jobId,
                        item_ids: [activeItemDetails.id],
                      },
                      {
                        onSuccess: (res) => {
                          setSaveFeedback({
                            saved_count: res.saved_count,
                            already_existing_count: res.already_existing_count,
                            message: res.message,
                          });
                          setActiveItemDetails(null);
                          refetch();
                        },
                      }
                    );
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold touch-manipulation"
                >
                  Save to CRM
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
