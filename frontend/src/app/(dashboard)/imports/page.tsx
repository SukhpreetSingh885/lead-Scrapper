"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2, ShieldCheck, Download } from "lucide-react";
import { Header } from "@/components/layout/header";
import { apiClient } from "@/lib/api-client";

export default function ImportsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [licenseName, setLicenseName] = useState("Commercial B2B Directory License 2026");
  const [permittedUsage, setPermittedUsage] = useState("Permitted Storage, Contact Enrichment & Lead Generation");
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select a .csv or .xlsx file to import.");
      return;
    }

    setIsUploading(true);
    setErrorMsg(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("license_name", licenseName);
    formData.append("permitted_usage", permittedUsage);

    try {
      const res = await apiClient<any>("/api/v1/leads/import", {
        method: "POST",
        body: formData,
      });
      setResult(res);
      setFile(null);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to import licensed lead file.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <Header
        title="Licensed Lead Import"
        subtitle="Import verified CSV or XLSX commercial datasets with compliance provenance tracking."
      />

      {/* Compliance Note */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 flex items-start space-x-3">
        <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-slate-900">Compliance & Provenance Verification</div>
          <p className="text-[11px] leading-relaxed text-slate-600">
            Imported records are stored with full source licensing attribution. All incoming records
            undergo automated Indian phone normalization (+91 E.164) and multi-stage branch duplicate detection.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {result && (
        <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs space-y-3">
          <div className="flex items-center space-x-2 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>Dataset Successfully Imported</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white p-3 rounded-lg border border-emerald-100 text-slate-700">
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold">Total Rows</span>
              <span className="font-bold text-sm">{result.total_parsed}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold">New Inserted</span>
              <span className="font-bold text-sm text-emerald-600">{result.inserted}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold">Updated Duplicates</span>
              <span className="font-bold text-sm text-blue-600">{result.updated}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold">Review Flagged</span>
              <span className="font-bold text-sm text-amber-600">{result.duplicates_flagged}</span>
            </div>
          </div>
          <div className="flex justify-end">
            <Link
              href="/leads"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg text-xs"
            >
              View Saved Leads
            </Link>
          </div>
        </div>
      )}

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5 text-xs">
        <div>
          <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Select Spreadsheet (.csv or .xlsx)
          </label>
          <div className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-xl p-8 text-center cursor-pointer transition-colors relative">
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <div className="font-semibold text-slate-800 text-sm">
              {file ? file.name : "Click to select or drag and drop lead spreadsheet"}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Supports CSV with UTF-8 encoding or Excel XLSX
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Source License Name
            </label>
            <input
              type="text"
              value={licenseName}
              onChange={(e) => setLicenseName(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Permitted Usage Scope
            </label>
            <input
              type="text"
              value={permittedUsage}
              onChange={(e) => setPermittedUsage(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
          <div className="text-[11px] text-slate-400">
            A sample template is available in <code>data/sample/sample_licensed_leads.csv</code>
          </div>

          <button
            type="submit"
            disabled={isUploading || !file}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Importing & Deduplicating...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Start Import</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

