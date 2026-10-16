"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Search,
  Download,
  Filter,
  CheckCircle,
  ExternalLink,
  Phone,
  Mail,
  Globe,
  MessageSquare,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { LeadListItem } from "@/types";
import { formatPhoneNumber, formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useCreateExport } from "@/hooks/use-exports";

interface LeadsTableProps {
  leads: LeadListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onSearchChange: (query: string) => void;
  isLoading?: boolean;
}

export function LeadsTable({
  leads,
  total,
  page,
  pageSize,
  onPageChange,
  onSearchChange,
  isLoading,
}: LeadsTableProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [exportFormat, setExportFormat] = useState<"csv" | "xlsx">("csv");
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const { mutate: createExport, isPending: isExporting } = useCreateExport();

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

  const handleExport = (format: "csv" | "xlsx") => {
    setExportNotice(null);
    createExport(
      {
        file_format: format,
        selected_ids: selectedIds.length > 0 ? selectedIds : undefined,
      },
      {
        onSuccess: (data) => {
          setExportNotice(
            `Export job created (${data.row_count} leads). Download ready at: ${data.download_url}`
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

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Table Toolbar */}
      <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search leads by name, city, address, or phone..."
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value);
                onSearchChange(e.target.value);
              }}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {selectedIds.length > 0 && (
            <span className="text-xs text-slate-500 font-medium mr-2">
              {selectedIds.length} selected
            </span>
          )}

          <button
            onClick={() => handleExport("csv")}
            disabled={isExporting || total === 0}
            className="px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 flex items-center space-x-1.5 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={() => handleExport("xlsx")}
            disabled={isExporting || total === 0}
            className="px-3 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white flex items-center space-x-1.5 disabled:opacity-50 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Excel</span>
          </button>
        </div>
      </div>

      {exportNotice && (
        <div className="p-3 bg-blue-50 border-b border-blue-200 text-xs text-blue-800 flex items-center justify-between">
          <span>{exportNotice}</span>
          <button
            onClick={() => setExportNotice(null)}
            className="text-blue-600 hover:text-blue-900 font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Table */}
      <div className="overflow-x-auto min-h-[350px]">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <th className="py-3 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={selectedIds.length === leads.length && leads.length > 0}
                  onChange={handleSelectAll}
                  className="rounded text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                />
              </th>
              <th className="py-3 px-3">Business Name & Branch</th>
              <th className="py-3 px-3">Category</th>
              <th className="py-3 px-3">Mobile (+91)</th>
              <th className="py-3 px-3">WhatsApp</th>
              <th className="py-3 px-3">Email</th>
              <th className="py-3 px-3">Location (City, State)</th>
              <th className="py-3 px-3">Website</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3">Source</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {isLoading ? (
              <tr>
                <td colSpan={11} className="py-12 text-center text-slate-400">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent mb-2"></div>
                  <div>Loading eligible business leads...</div>
                </td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={11} className="py-12 text-center text-slate-500">
                  <div className="text-base font-semibold text-slate-800 mb-1">
                    No leads found
                  </div>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                    No leads match your current query. Try searching for a location or business category.
                  </p>
                  <Link
                    href="/search"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"
                  >
                    Find Leads Now
                  </Link>
                </td>
              </tr>
            ) : (
              leads.map((lead) => {
                const isSelected = selectedIds.includes(lead.id);
                return (
                  <tr
                    key={lead.id}
                    className={`hover:bg-slate-50/80 transition-colors ${
                      isSelected ? "bg-blue-50/50" : ""
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
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-900 hover:text-blue-600 transition-colors">
                        <Link href={`/leads/${lead.id}`}>
                          {lead.business_name}
                        </Link>
                      </div>
                      {lead.address_line && (
                        <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                          {lead.address_line}
                        </div>
                      )}
                    </td>

                    {/* Category */}
                    <td className="py-3 px-3">
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px]">
                        {lead.category}
                      </span>
                    </td>

                    {/* Mobile */}
                    <td className="py-3 px-3 font-mono text-[11px]">
                      {lead.primary_mobile ? (
                        <span className="text-slate-900 font-medium">
                          {formatPhoneNumber(lead.primary_mobile)}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">Not Available</span>
                      )}
                    </td>

                    {/* WhatsApp */}
                    <td className="py-3 px-3 font-mono text-[11px]">
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
                    <td className="py-3 px-3 text-[11px]">
                      {lead.primary_email ? (
                        <a
                          href={`mailto:${lead.primary_email}`}
                          className="text-blue-600 hover:underline flex items-center space-x-1"
                        >
                          <Mail className="w-3 h-3 shrink-0" />
                          <span className="line-clamp-1">{lead.primary_email}</span>
                        </a>
                      ) : (
                        <span className="text-slate-400 italic">Not Available</span>
                      )}
                    </td>

                    {/* City & State */}
                    <td className="py-3 px-3">
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
                    <td className="py-3 px-3">
                      {lead.enrichment_status === "completed" ? (
                        <Badge variant="success">Enriched</Badge>
                      ) : lead.enrichment_status === "running" ? (
                        <Badge variant="warning">Enriching...</Badge>
                      ) : (
                        <Badge variant="secondary">Pending</Badge>
                      )}
                    </td>

                    {/* Source */}
                    <td className="py-3 px-3">
                      {lead.is_demo ? (
                        <Badge variant="demo">DEMO DATA</Badge>
                      ) : (
                        <span className="text-[11px] text-slate-600">
                          {lead.source_name || "Licensed"}
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/leads/${lead.id}`}
                        className="px-2.5 py-1 text-[11px] font-medium rounded border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors inline-block"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
        <div>
          Showing {leads.length > 0 ? (page - 1) * pageSize + 1 : 0} to{" "}
          {Math.min(page * pageSize, total)} of {total} unique leads
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="p-1.5 rounded border border-slate-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-medium text-slate-800">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-1.5 rounded border border-slate-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

