"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  Download,
  CheckCircle,
  ExternalLink,
  Phone,
  Smartphone,
  Mail,
  Globe,
  MessageSquare,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Trash2,
  AlertTriangle,
  Loader2,
  X,
  PhoneCall,
  MapPin,
} from "lucide-react";
import { LeadListItem } from "@/types";
import { formatPhoneNumber } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useCreateExport } from "@/hooks/use-exports";
import { useDeleteLead, useBulkDeleteLeads } from "@/hooks/use-leads";

interface LeadsTableProps {
  leads: LeadListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onSearchChange: (query: string) => void;
  isLoading?: boolean;
  filterCity?: string;
  filterCategory?: string;
  filterJobId?: string;
  hasContactNumber?: boolean;
  onResetFilters?: () => void;
  totalSavedLeads?: number;
}

export function LeadsTable({
  leads,
  total,
  page,
  pageSize,
  onPageChange,
  onSearchChange,
  isLoading,
  filterCity,
  filterCategory,
  filterJobId,
  hasContactNumber,
  onResetFilters,
  totalSavedLeads,
}: LeadsTableProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // Deletion modals state
  const [singleDeleteTarget, setSingleDeleteTarget] = useState<LeadListItem | null>(null);
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [showFilteredDeleteModal, setShowFilteredDeleteModal] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const { mutate: createExport, isPending: isExporting } = useCreateExport();
  const deleteLeadMutation = useDeleteLead();
  const bulkDeleteMutation = useBulkDeleteLeads();

  // Close modals on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSingleDeleteTarget(null);
        setShowBulkDeleteModal(false);
        setShowFilteredDeleteModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(leads.map((l) => l.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectedLeads = leads.filter((l) => selectedIds.includes(l.id));
  const qualifiedSelectedCount = selectedLeads.filter(
    (l) => Boolean(l.primary_mobile || l.primary_landline || l.primary_whatsapp)
  ).length;

  // Export handler supporting selected, category, or contact qualified
  const handleExport = (
    format: "csv" | "xlsx",
    options?: { exportCategory?: boolean; contactQualifiedOnly?: boolean }
  ) => {
    setExportNotice(null);

    if (selectedIds.length > 0 && !options?.exportCategory && !options?.contactQualifiedOnly) {
      if (qualifiedSelectedCount === 0) {
        setExportNotice("None of the selected leads have a valid contact number (Mobile, Landline, or WhatsApp). Exports require at least one valid contact number.");
        return;
      }
    }

    createExport(
      {
        file_format: format,
        selected_ids:
          options?.exportCategory || options?.contactQualifiedOnly
            ? undefined
            : selectedIds.length > 0
            ? selectedIds
            : undefined,
        city: filterCity || undefined,
        category: filterCategory || undefined,
        job_id: filterJobId || undefined,
        has_contact_number: true,
        contact_qualified: true,
      },
      {
        onSuccess: (data) => {
          const downloadName = data.filename || `leads-export.${data.file_format}`;
          setExportNotice(
            `Export ready: ${downloadName} (${data.row_count} unique leads). Download started.`
          );
          if (data.download_url) {
            window.open(data.download_url, "_blank");
          }
        },
        onError: (err: any) => {
          setExportNotice(`Export failed: ${err.message}`);
        },
      }
    );
  };

  // Confirm and execute single lead delete
  const executeSingleDelete = () => {
    if (!singleDeleteTarget) return;
    deleteLeadMutation.mutate(singleDeleteTarget.id, {
      onSuccess: () => {
        setActionMessage(`Successfully deleted "${singleDeleteTarget.business_name}".`);
        setSingleDeleteTarget(null);
        setSelectedIds((prev) => prev.filter((id) => id !== singleDeleteTarget.id));
      },
      onError: (err: any) => {
        setActionMessage(`Failed to delete lead: ${err.message}`);
      },
    });
  };

  // Confirm and execute bulk delete of selected leads
  const executeBulkDelete = () => {
    if (selectedIds.length === 0) return;
    bulkDeleteMutation.mutate(
      {
        lead_ids: selectedIds,
      },
      {
        onSuccess: (res) => {
          setActionMessage(res.message);
          setSelectedIds([]);
          setShowBulkDeleteModal(false);
        },
        onError: (err: any) => {
          setActionMessage(`Failed to delete leads: ${err.message}`);
        },
      }
    );
  };

  // Confirm and execute delete of all filtered leads
  const executeFilteredDelete = () => {
    bulkDeleteMutation.mutate(
      {
        delete_all_filtered: true,
        filters: {
          city: filterCity || undefined,
          category: filterCategory || undefined,
          job_id: filterJobId || undefined,
          has_contact_number: hasContactNumber || undefined,
          query: searchInput || undefined,
        },
      },
      {
        onSuccess: (res) => {
          setActionMessage(res.message);
          setSelectedIds([]);
          setShowFilteredDeleteModal(false);
        },
        onError: (err: any) => {
          setActionMessage(`Failed to delete filtered leads: ${err.message}`);
        },
      }
    );
  };

  const isAnyFilterActive = Boolean(
    filterCity || filterCategory || filterJobId || hasContactNumber || searchInput
  );
  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden w-full min-w-0">
      {/* Table Toolbar */}
      <div className="p-3 sm:p-4 border-b border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-50/50">
        <div className="flex items-center space-x-3 flex-1 w-full md:max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search saved leads by name, city, address, or phone..."
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value);
                onSearchChange(e.target.value);
              }}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white min-h-[38px]"
            />
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-1.5 sm:gap-2">
          {selectedIds.length > 0 && (
            <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
              {selectedIds.length} Selected ({qualifiedSelectedCount} export-eligible)
            </span>
          )}

          {/* Bulk Delete Selected Button */}
          {selectedIds.length > 0 && (
            <button
              onClick={() => setShowBulkDeleteModal(true)}
              className="px-2.5 sm:px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 flex items-center space-x-1 transition touch-manipulation min-h-[36px]"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-600 shrink-0" />
              <span>Delete Selected ({selectedIds.length})</span>
            </button>
          )}

          {/* Delete All Filtered Button */}
          {isAnyFilterActive && total > 0 && (
            <button
              onClick={() => setShowFilteredDeleteModal(true)}
              className="px-2.5 sm:px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 flex items-center space-x-1 transition touch-manipulation min-h-[36px]"
              title="Delete all leads matching current active filters"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-600 shrink-0" />
              <span>Delete All Filtered ({total})</span>
            </button>
          )}

          {/* Export Contact Qualified Button */}
          <button
            onClick={() => handleExport("xlsx", { contactQualifiedOnly: true })}
            disabled={isExporting || total === 0}
            className="px-2.5 sm:px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100 flex items-center space-x-1.5 transition disabled:opacity-50 touch-manipulation min-h-[36px]"
            title="Exports only businesses with at least one verified phone/mobile/whatsapp"
          >
            <PhoneCall className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Qualified (XLSX)</span>
          </button>

          {/* Export CSV / XLSX */}
          <button
            onClick={() => handleExport("csv")}
            disabled={isExporting || total === 0 || (selectedIds.length > 0 && qualifiedSelectedCount === 0)}
            className="px-2.5 sm:px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 flex items-center space-x-1.5 transition disabled:opacity-50 touch-manipulation min-h-[36px]"
          >
            <Download className="w-3.5 h-3.5 shrink-0" />
            <span>{selectedIds.length > 0 ? `CSV (${qualifiedSelectedCount} eligible)` : "Export CSV"}</span>
          </button>

          <button
            onClick={() => handleExport("xlsx")}
            disabled={isExporting || total === 0 || (selectedIds.length > 0 && qualifiedSelectedCount === 0)}
            className="px-2.5 sm:px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-1.5 transition disabled:opacity-50 shadow-xs touch-manipulation min-h-[36px]"
          >
            <Download className="w-3.5 h-3.5 shrink-0" />
            <span>{selectedIds.length > 0 ? `Excel (${qualifiedSelectedCount} eligible)` : "Export Excel"}</span>
          </button>
        </div>
      </div>

      {/* Notices & Banners */}
      {exportNotice && (
        <div className="p-3 bg-blue-50 border-b border-blue-200 text-xs text-blue-900 flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2 min-w-0">
            <CheckCircle className="w-4 h-4 text-blue-600 shrink-0" />
            <span className="truncate">{exportNotice}</span>
          </div>
          <button
            onClick={() => setExportNotice(null)}
            className="text-blue-600 hover:text-blue-900 font-bold shrink-0 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {actionMessage && (
        <div className="p-3 bg-slate-100 border-b border-slate-200 text-xs text-slate-800 flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2 min-w-0">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="truncate">{actionMessage}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-slate-500 hover:text-slate-800 font-bold shrink-0 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* =========================================================================
          MOBILE LEAD-CARD VIEW (< 768px / md:hidden)
          Clean, fully accessible cards with selection checkboxes and all contact info
         ========================================================================= */}
      <div className="md:hidden">
        {isLoading ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
            <div>Loading eligible business leads...</div>
          </div>
        ) : leads.length === 0 ? (
          <div className="p-6 text-center text-slate-500 space-y-3">
            <div className="text-base font-semibold text-slate-800">
              {isAnyFilterActive ? "No saved leads match your filters" : "No leads found in database"}
            </div>
            <p className="text-xs text-slate-400 max-w-xs mx-auto">
              {isAnyFilterActive
                ? "Try clearing some filters or searching for another city/category."
                : "No business leads saved yet. Start discovery search to find real businesses."}
            </p>
            {isAnyFilterActive && onResetFilters && (
              <button
                type="button"
                onClick={onResetFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold"
              >
                Reset Filters
              </button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {/* Mobile Select All Header */}
            <div className="p-3 bg-slate-100/60 flex items-center justify-between text-xs text-slate-700">
              <label className="flex items-center space-x-2 cursor-pointer touch-manipulation">
                <input
                  type="checkbox"
                  checked={selectedIds.length === leads.length && leads.length > 0}
                  onChange={handleSelectAll}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
                />
                <span className="font-semibold">Select All ({leads.length} on page)</span>
              </label>
              {selectedIds.length > 0 && (
                <span className="text-blue-700 font-semibold">{selectedIds.length} chosen</span>
              )}
            </div>

            {leads.map((lead) => {
              const isSelected = selectedIds.includes(lead.id);
              return (
                <div
                  key={lead.id}
                  className={`p-3.5 space-y-2.5 transition-colors ${
                    isSelected ? "bg-blue-50/40" : "bg-white"
                  }`}
                >
                  {/* Top row: Checkbox, Name, Category, Status */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start space-x-2.5 min-w-0 flex-1">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleSelectRow(lead.id)}
                        className="mt-1 rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
                      />
                      <div className="min-w-0 flex-1">
                        <Link
                          href={`/leads/${lead.id}`}
                          className="font-bold text-slate-900 text-sm hover:text-blue-600 transition-colors break-words block leading-tight"
                        >
                          {lead.business_name}
                        </Link>
                        <div className="inline-block mt-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[10px]">
                          {lead.category}
                        </div>
                      </div>
                    </div>

                    <div className="shrink-0 text-right">
                      {lead.enrichment_status === "completed" ? (
                        <Badge variant="success" className="text-[9px]">Enriched</Badge>
                      ) : lead.enrichment_status === "running" ? (
                        <Badge variant="warning" className="text-[9px]">Enriching...</Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[9px]">Saved</Badge>
                      )}
                    </div>
                  </div>

                  {/* Physical Address */}
                  <div className="pl-6 text-xs text-slate-600 space-y-0.5">
                    {lead.address_line && (
                      <div className="text-[11px] text-slate-500 line-clamp-2">{lead.address_line}</div>
                    )}
                    <div className="text-[11px] text-slate-700 font-medium flex items-center space-x-1">
                      <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>{lead.city}, {lead.state}</span>
                    </div>
                  </div>

                  {/* Contacts Grid: Mobile, WhatsApp, Email */}
                  <div className="pl-6 pt-1 space-y-1 text-xs">
                    {lead.primary_mobile ? (
                      <div className="flex items-center space-x-1.5 font-mono text-slate-800">
                        <Smartphone className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <a href={`tel:${lead.primary_mobile}`} className="hover:underline">
                          {formatPhoneNumber(lead.primary_mobile)}
                        </a>
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-400 italic">No mobile number</div>
                    )}

                    {lead.primary_whatsapp && (
                      <div className="flex items-center space-x-1.5 font-mono text-emerald-700">
                        <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                        <a
                          href={`https://wa.me/${lead.primary_whatsapp.replace(/\D/g, "")}`}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:underline"
                        >
                          WhatsApp: {formatPhoneNumber(lead.primary_whatsapp)}
                        </a>
                      </div>
                    )}

                    {lead.primary_email && (
                      <div className="flex items-center space-x-1.5 text-blue-700 truncate">
                        <Mail className="w-3.5 h-3.5 shrink-0" />
                        <a href={`mailto:${lead.primary_email}`} className="hover:underline truncate">
                          {lead.primary_email}
                        </a>
                      </div>
                    )}

                    {lead.website_url && (
                      <div className="flex items-center space-x-1.5 text-blue-600 truncate">
                        <Globe className="w-3.5 h-3.5 shrink-0" />
                        <a
                          href={lead.website_url}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:underline truncate"
                        >
                          {lead.website_url.replace(/^https?:\/\//, "")}
                        </a>
                      </div>
                    )}
                  </div>

                  {/* Bottom Row: Actions */}
                  <div className="pl-6 pt-2 border-t border-slate-100 flex items-center justify-between">
                    <Link
                      href={`/leads/${lead.id}`}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition touch-manipulation"
                    >
                      View Details
                    </Link>

                    <button
                      type="button"
                      onClick={() => setSingleDeleteTarget(lead)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded hover:bg-rose-50 transition touch-manipulation"
                      title="Delete Lead"
                      aria-label={`Delete ${lead.business_name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* =========================================================================
          DESKTOP & TABLET DATA TABLE (>= 768px / hidden md:block)
          Preserves the exact multi-column table layout with horizontal scrolling
         ========================================================================= */}
      <div className="hidden md:block overflow-x-auto min-h-[350px]">
        <table className="w-full text-left border-collapse text-xs min-w-[900px]">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={selectedIds.length === leads.length && leads.length > 0}
                  onChange={handleSelectAll}
                  className="rounded text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                />
              </th>
              <th className="py-3 px-3">Business Name &amp; Branch</th>
              <th className="py-3 px-3">Category</th>
              <th className="py-3 px-3">Mobile (+91)</th>
              <th className="py-3 px-3">WhatsApp</th>
              <th className="py-3 px-3">Email</th>
              <th className="py-3 px-3">Location (City, State)</th>
              <th className="py-3 px-3">Website</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {isLoading ? (
              <tr>
                <td colSpan={10} className="py-12 text-center text-slate-400">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
                  <div>Loading eligible business leads...</div>
                </td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-12 text-center text-slate-500">
                  <div className="text-base font-semibold text-slate-800 mb-1">
                    {isAnyFilterActive ? "No saved leads match your filters" : "No leads found in database"}
                  </div>
                  <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
                    {isAnyFilterActive ? (
                      totalSavedLeads && totalSavedLeads > 0
                        ? `There are ${totalSavedLeads} total saved leads in your CRM, but none match the current filter criteria.`
                        : "No saved leads match your current filter criteria."
                    ) : (
                      "No business leads have been saved to the CRM yet. Use the Discovery search to find and save verified Indian leads."
                    )}
                  </p>

                  {filterJobId && (
                    <div className="mb-4 max-w-lg mx-auto p-3 bg-amber-50/80 border border-amber-200 rounded-lg text-left text-xs text-amber-900 flex items-start space-x-2">
                      <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold">Search Job Isolation Active ({filterJobId.slice(0, 8)}): </span>
                        Leads discovered in this search job remain in temporary preview storage on the Search page until you explicitly save them.
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-center gap-3">
                    {isAnyFilterActive ? (
                      <>
                        {onResetFilters ? (
                          <button
                            type="button"
                            onClick={onResetFilters}
                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition"
                          >
                            Reset Filters (View All Saved Leads)
                          </button>
                        ) : (
                          <Link
                            href="/leads"
                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition"
                          >
                            Reset Filters (View All Saved Leads)
                          </Link>
                        )}
                        {filterJobId && (
                          <Link
                            href="/search"
                            className="inline-flex items-center px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50 transition"
                          >
                            Go to Search Discovery Preview
                          </Link>
                        )}
                      </>
                    ) : (
                      <Link
                        href="/search"
                        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition"
                      >
                        Find Business Leads
                      </Link>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              leads.map((lead) => {
                const isSelected = selectedIds.includes(lead.id);
                return (
                  <tr
                    key={lead.id}
                    className={`hover:bg-slate-50/80 transition-colors ${
                      isSelected ? "bg-blue-50/40" : ""
                    }`}
                  >
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleSelectRow(lead.id)}
                        className="rounded text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                      />
                    </td>

                    {/* Business Name */}
                    <td className="py-3 px-3 max-w-xs">
                      <div className="font-semibold text-slate-900 hover:text-blue-600 transition-colors truncate">
                        <Link href={`/leads/${lead.id}`}>
                          {lead.business_name}
                        </Link>
                      </div>
                      {lead.address_line && (
                        <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5 truncate">
                          {lead.address_line}
                        </div>
                      )}
                    </td>

                    {/* Category */}
                    <td className="py-3 px-3">
                      <span className="inline-block px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-medium whitespace-nowrap">
                        {lead.category}
                      </span>
                    </td>

                    {/* Mobile */}
                    <td className="py-3 px-3 font-mono text-[11px] whitespace-nowrap">
                      {lead.primary_mobile ? (
                        <span className="text-slate-900 font-medium">
                          {formatPhoneNumber(lead.primary_mobile)}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">Not Available</span>
                      )}
                    </td>

                    {/* WhatsApp */}
                    <td className="py-3 px-3 font-mono text-[11px] whitespace-nowrap">
                      {lead.primary_whatsapp ? (
                        <a
                          href={`https://wa.me/${lead.primary_whatsapp.replace(/\D/g, "")}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-600 hover:underline flex items-center space-x-1"
                        >
                          <MessageSquare className="w-3 h-3 shrink-0" />
                          <span>{formatPhoneNumber(lead.primary_whatsapp)}</span>
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">Not Available</span>
                      )}
                    </td>

                    {/* Email */}
                    <td className="py-3 px-3 text-[11px] max-w-[140px] truncate">
                      {lead.primary_email ? (
                        <a
                          href={`mailto:${lead.primary_email}`}
                          className="text-blue-600 hover:underline flex items-center space-x-1 truncate"
                        >
                          <Mail className="w-3 h-3 shrink-0" />
                          <span className="truncate">{lead.primary_email}</span>
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">Not Available</span>
                      )}
                    </td>

                    {/* City & State */}
                    <td className="py-3 px-3 whitespace-nowrap">
                      <div className="text-slate-800 font-medium">{lead.city}</div>
                      <div className="text-[10px] text-slate-400">{lead.state}</div>
                    </td>

                    {/* Website */}
                    <td className="py-3 px-3">
                      {lead.website_url ? (
                        <a
                          href={lead.website_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 hover:underline inline-flex items-center space-x-1 text-[11px]"
                        >
                          <Globe className="w-3 h-3 shrink-0" />
                          <span className="max-w-[120px] truncate">
                            {lead.website_url.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                          </span>
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">Not Available</span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="py-3 px-3 whitespace-nowrap">
                      {lead.enrichment_status === "completed" ? (
                        <Badge variant="success" className="text-[10px]">Enriched</Badge>
                      ) : lead.enrichment_status === "running" ? (
                        <Badge variant="warning" className="text-[10px]">Enriching...</Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px]">Saved</Badge>
                      )}
                    </td>

                    {/* Actions: Details & Delete */}
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end space-x-1.5">
                        <Link
                          href={`/leads/${lead.id}`}
                          className="px-2.5 py-1 text-[11px] font-medium rounded border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors inline-block"
                        >
                          Details
                        </Link>
                        <button
                          type="button"
                          onClick={() => setSingleDeleteTarget(lead)}
                          className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-rose-50 transition-colors"
                          title="Delete Lead from CRM"
                          aria-label={`Delete ${lead.business_name}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer (Responsive stack on mobile) */}
      <div className="p-3.5 sm:p-4 border-t border-slate-200 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
        <div className="text-center sm:text-left">
          Showing {leads.length > 0 ? (page - 1) * pageSize + 1 : 0} to{" "}
          {Math.min(page * pageSize, total)} of {total} unique saved leads
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="p-1.5 rounded-lg border border-slate-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation min-w-[34px] min-h-[34px] flex items-center justify-center"
            aria-label="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-medium text-slate-800 px-1">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-1.5 rounded-lg border border-slate-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation min-w-[34px] min-h-[34px] flex items-center justify-center"
            aria-label="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Single Lead Delete Confirmation Modal */}
      {singleDeleteTarget && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150"
          onClick={() => setSingleDeleteTarget(null)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full p-5 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start space-x-3">
              <div className="p-2.5 rounded-full bg-rose-100 text-rose-600 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="font-bold text-base text-slate-900">Delete Business Lead?</h4>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Are you sure you want to permanently delete <strong className="break-words">{singleDeleteTarget.business_name}</strong>? All associated contacts and enrichment records will be permanently removed.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSingleDeleteTarget(null)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 touch-manipulation"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={executeSingleDelete}
                disabled={deleteLeadMutation.isPending}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5 touch-manipulation"
              >
                {deleteLeadMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5 shrink-0" />
                    <span>Delete Lead</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Selected Leads Modal */}
      {showBulkDeleteModal && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150"
          onClick={() => setShowBulkDeleteModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full p-5 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start space-x-3">
              <div className="p-2.5 rounded-full bg-rose-100 text-rose-600 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="font-bold text-base text-slate-900">Delete {selectedIds.length} Selected Leads?</h4>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Are you sure you want to delete the <strong>{selectedIds.length}</strong> selected business leads? They will be permanently removed from your CRM.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowBulkDeleteModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 touch-manipulation"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={executeBulkDelete}
                disabled={bulkDeleteMutation.isPending}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5 touch-manipulation"
              >
                {bulkDeleteMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5 shrink-0" />
                    <span>Delete Selected Leads</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete All Filtered Leads Modal */}
      {showFilteredDeleteModal && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150"
          onClick={() => setShowFilteredDeleteModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full p-5 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start space-x-3">
              <div className="p-2.5 rounded-full bg-rose-100 text-rose-600 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="font-bold text-base text-slate-900">Delete All {total} Filtered Leads?</h4>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  This will permanently delete <strong>{total}</strong> leads matching your current active filter criteria. Unfiltered leads will remain safe.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowFilteredDeleteModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 touch-manipulation"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={executeFilteredDelete}
                disabled={bulkDeleteMutation.isPending}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5 touch-manipulation"
              >
                {bulkDeleteMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                    <span>Deleting All {total} Leads...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5 shrink-0" />
                    <span>Delete All {total} Leads</span>
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
