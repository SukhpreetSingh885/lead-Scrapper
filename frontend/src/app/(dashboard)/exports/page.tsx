"use client";

import React, { useState } from "react";
import { Download, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2, ShieldAlert } from "lucide-react";
import { Header } from "@/components/layout/header";
import { useCreateExport } from "@/hooks/use-exports";
import { formatBytes } from "@/lib/utils";

export default function ExportsPage() {
  const [format, setFormat] = useState<"csv" | "xlsx">("csv");
  const [hasMobileOnly, setHasMobileOnly] = useState(false);
  const [hasEmailOnly, setHasEmailOnly] = useState(false);
  const [cityFilter, setCityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const [recentExport, setRecentExport] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { mutate: createExport, isPending } = useCreateExport();

  const handleCreateExport = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setRecentExport(null);

    createExport(
      {
        file_format: format,
        city: cityFilter || undefined,
        category: categoryFilter || undefined,
        has_mobile: hasMobileOnly || undefined,
        has_email: hasEmailOnly || undefined,
      },
      {
        onSuccess: (data) => {
          setRecentExport(data);
          if (data.download_url) {
            window.open(data.download_url, "_blank");
          }
        },
        onError: (err: any) => {
          setErrorMsg(err.message || "Failed to generate export file.");
        },
      }
    );
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <Header
        title="Export Leads"
        subtitle="Download eligible unique business leads in CSV or Excel (XLSX) format with formula sanitization."
      />

      {/* Security & Sourcing Compliance Note */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 flex items-start space-x-3">
        <ShieldAlert className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-slate-900">Export Compliance & Formula Injection Safeguards</div>
          <p className="text-[11px] leading-relaxed text-slate-600">
            Exports strictly exclude provider-restricted discovery previews. Only independently sourced or
            licensed CRM leads are included. All text cells beginning with formula triggers (<code>=</code>, <code>+</code>, <code>-</code>, <code>@</code>)
            are automatically sanitized with apostrophes to protect spreadsheet users.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {recentExport && (
        <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs space-y-3">
          <div className="flex items-center space-x-2 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>Export File Generated Successfully</span>
          </div>
          <div className="text-slate-700">
            Exported <strong>{recentExport.row_count}</strong> eligible unique leads (
            {formatBytes(recentExport.file_size_bytes)}).
          </div>
          {recentExport.download_url && (
            <div>
              <a
                href={recentExport.download_url}
                download
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold text-xs transition-colors shadow-sm"
              >
                <Download className="w-4 h-4" />
                <span>Click to Download File Again</span>
              </a>
            </div>
          )}
        </div>
      )}

      {/* Export Options Form */}
      <form onSubmit={handleCreateExport} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5 text-xs">
        <div>
          <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Export File Format
          </label>
          <div className="grid grid-cols-2 gap-4">
            <label
              className={`p-4 rounded-xl border cursor-pointer flex items-center space-x-3 transition-colors ${
                format === "csv"
                  ? "border-blue-500 bg-blue-50/40 text-blue-900"
                  : "border-slate-200 hover:bg-slate-50 text-slate-700"
              }`}
            >
              <input
                type="radio"
                name="format"
                value="csv"
                checked={format === "csv"}
                onChange={() => setFormat("csv")}
                className="text-blue-600"
              />
              <div>
                <div className="font-bold">Standard CSV</div>
                <div className="text-[11px] text-slate-500">
                  UTF-8 BOM encoded for seamless opening in Excel and CRM tools.
                </div>
              </div>
            </label>

            <label
              className={`p-4 rounded-xl border cursor-pointer flex items-center space-x-3 transition-colors ${
                format === "xlsx"
                  ? "border-emerald-500 bg-emerald-50/40 text-emerald-900"
                  : "border-slate-200 hover:bg-slate-50 text-slate-700"
              }`}
            >
              <input
                type="radio"
                name="format"
                value="xlsx"
                checked={format === "xlsx"}
                onChange={() => setFormat("xlsx")}
                className="text-emerald-600"
              />
              <div>
                <div className="font-bold">Microsoft Excel (.xlsx)</div>
                <div className="text-[11px] text-slate-500">
                  Styled headers, freeze panes, and auto-adjusted columns.
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Filter Criteria */}
        <div className="pt-3 border-t border-slate-100 space-y-3">
          <label className="block font-semibold text-slate-700 uppercase tracking-wider">
            Lead Filter Criteria
          </label>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-500 mb-1">Filter by City (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Mohali"
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
                className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-slate-500 mb-1">Filter by Category (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Salon"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-4 pt-2">
            <label className="flex items-center space-x-2 cursor-pointer text-slate-700">
              <input
                type="checkbox"
                checked={hasMobileOnly}
                onChange={(e) => setHasMobileOnly(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span>Only export leads with a valid mobile number (+91)</span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer text-slate-700">
              <input
                type="checkbox"
                checked={hasEmailOnly}
                onChange={(e) => setHasEmailOnly(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span>Only export leads with a public business email</span>
            </label>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="text-[11px] text-slate-400">
            Selected leads on the All Leads table can also be exported directly.
          </div>

          <button
            type="submit"
            disabled={isPending}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating Export...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Download {format.toUpperCase()}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

