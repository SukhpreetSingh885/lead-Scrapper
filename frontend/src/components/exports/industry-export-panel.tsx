"use client";

import React, { useState, useEffect } from "react";
import {
  Download,
  FileSpreadsheet,
  FileText,
  Archive,
  Layers,
  Building2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  X,
  PhoneCall,
  AlertTriangle,
} from "lucide-react";
import { useExportIndustries, useCreateExport } from "@/hooks/use-exports";
import { ExportItem } from "@/types";
import { formatBytes } from "@/lib/utils";

interface IndustryExportPanelProps {
  initialCategory?: string;
  className?: string;
}

export function IndustryExportPanel({
  initialCategory,
  className = "",
}: IndustryExportPanelProps) {
  const { data: industries, isLoading: loadingIndustries } = useExportIndustries();
  const { mutate: createExport, isPending: isExporting } = useCreateExport();

  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [fileFormat, setFileFormat] = useState<"xlsx" | "csv">("xlsx");
  const [recentExport, setRecentExport] = useState<ExportItem | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);

  // Set default category when industries load
  useEffect(() => {
    if (industries && industries.length > 0) {
      if (initialCategory) {
        const match = industries.find(
          (i) => i.category.toLowerCase() === initialCategory.toLowerCase()
        );
        if (match) {
          setSelectedCategory(match.category);
          return;
        }
      }
      if (!selectedCategory) {
        // Default to the industry with highest qualified leads
        const best = [...industries].sort((a, b) => b.qualified_leads - a.qualified_leads)[0];
        setSelectedCategory(best?.category || industries[0].category);
      }
    }
  }, [industries, initialCategory, selectedCategory]);

  const selectedIndustryObj = industries?.find((i) => i.category === selectedCategory);
  const totalEligibleAcrossAll = industries
    ? industries.reduce((acc, i) => acc + i.qualified_leads, 0)
    : 0;
  const eligibleIndustriesCount = industries
    ? industries.filter((i) => i.qualified_leads > 0).length
    : 0;

  const handleExportTrigger = (
    mode: "single" | "all_combined" | "all_separate_zip",
    actionKey: string
  ) => {
    setErrorMessage(null);
    setRecentExport(null);

    // Rule 13: Prevent empty file creation
    if (mode === "single" && (!selectedIndustryObj || selectedIndustryObj.qualified_leads === 0)) {
      setErrorMessage(
        `Category '${selectedCategory}' has 0 contact-qualified leads with valid contact numbers. Cannot generate empty export.`
      );
      return;
    }

    if ((mode === "all_combined" || mode === "all_separate_zip") && totalEligibleAcrossAll === 0) {
      setErrorMessage(
        "No contact-qualified leads available with valid phone/mobile/whatsapp numbers."
      );
      return;
    }

    setActiveAction(actionKey);

    createExport(
      {
        file_format: fileFormat,
        export_mode: mode,
        category: mode === "single" ? selectedCategory : undefined,
        contact_qualified: true,
      },
      {
        onSuccess: (data) => {
          setRecentExport(data);
          setActiveAction(null);
          if (data.download_url) {
            window.open(data.download_url, "_blank");
          }
        },
        onError: (err: any) => {
          setErrorMessage(err.message || "Failed to generate export file.");
          setActiveAction(null);
        },
      }
    );
  };

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 space-y-4 w-full min-w-0 ${className}`}
    >
      {/* Header and Compliance Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-slate-100">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-blue-600 shrink-0" />
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Industry-Wise Exports
            </h3>
          </div>
          <p className="text-[11px] text-slate-500">
            Download contact-qualified saved leads dynamically grouped by industry or combined as a single archive.
          </p>
        </div>

        <div className="flex items-center space-x-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-semibold px-2.5 py-1 rounded-lg self-start sm:self-auto">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>Mandatory Condition: Mobile OR Landline OR Advertised WhatsApp</span>
        </div>
      </div>

      {/* Controls Row: Industry Dropdown + Format Toggle */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
        {/* Industry Selector */}
        <div className="md:col-span-2 space-y-1">
          <div className="flex items-center justify-between">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider">
              Select Business Industry
            </label>
            {selectedIndustryObj && (
              <span className="text-[11px] font-semibold text-emerald-700">
                {selectedIndustryObj.qualified_leads} export-eligible leads
              </span>
            )}
          </div>
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              disabled={loadingIndustries || !industries || industries.length === 0}
              className="w-full pl-3 pr-8 py-2 text-xs font-medium rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[38px] disabled:opacity-50 appearance-none cursor-pointer"
            >
              {loadingIndustries ? (
                <option value="">Loading industries from database...</option>
              ) : industries && industries.length > 0 ? (
                industries.map((ind) => (
                  <option key={ind.slug} value={ind.category}>
                    {ind.category} — {ind.qualified_leads} export-eligible leads ({ind.total_leads} total in CRM)
                  </option>
                ))
              ) : (
                <option value="">No industry leads saved yet</option>
              )}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-slate-500">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* Format Selector */}
        <div className="space-y-1">
          <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider">
            File Format
          </label>
          <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200">
            <button
              type="button"
              onClick={() => setFileFormat("xlsx")}
              className={`flex items-center justify-center space-x-1.5 py-1.5 px-2 rounded-md text-xs font-semibold transition touch-manipulation ${
                fileFormat === "xlsx"
                  ? "bg-white text-emerald-700 shadow-2xs border border-emerald-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Excel (.xlsx)</span>
            </button>
            <button
              type="button"
              onClick={() => setFileFormat("csv")}
              className={`flex items-center justify-center space-x-1.5 py-1.5 px-2 rounded-md text-xs font-semibold transition touch-manipulation ${
                fileFormat === "csv"
                  ? "bg-white text-blue-700 shadow-2xs border border-blue-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              <span>CSV (.csv)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Pre-Download Eligibility Counter Banner (Rule 12) */}
      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2 text-slate-700 min-w-0">
          <PhoneCall className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span className="text-[11px] font-medium truncate">
            {selectedIndustryObj ? (
              <>
                <strong className="text-slate-900">{selectedIndustryObj.category}</strong>:{" "}
                <span className="font-bold text-emerald-700">
                  {selectedIndustryObj.qualified_leads} export-eligible leads
                </span>{" "}
                (with verified Mobile, Landline, or WhatsApp)
              </>
            ) : (
              "Select an industry to see export-eligible leads count"
            )}
          </span>
        </div>
        <div className="text-[11px] font-semibold text-slate-600">
          Global Database: <span className="text-blue-700 font-bold">{totalEligibleAcrossAll}</span> eligible across{" "}
          <span className="text-slate-900 font-bold">{eligibleIndustriesCount}</span> industries
        </div>
      </div>

      {/* Warning if selected category has 0 qualified leads (Rule 13) */}
      {selectedIndustryObj && selectedIndustryObj.qualified_leads === 0 && (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            Category <strong>{selectedIndustryObj.category}</strong> has 0 contact-qualified leads with valid contact numbers. Empty file generation is prevented.
          </span>
        </div>
      )}

      {/* Action Buttons: 3 Cards / Options */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
        {/* Action 1: Export Selected Industry */}
        <button
          type="button"
          disabled={isExporting || !selectedCategory || (selectedIndustryObj && selectedIndustryObj.qualified_leads === 0)}
          onClick={() => handleExportTrigger("single", "single")}
          className={`p-3 rounded-xl border text-left transition flex flex-col justify-between group touch-manipulation min-h-[92px] ${
            selectedIndustryObj && selectedIndustryObj.qualified_leads === 0
              ? "border-slate-200 bg-slate-50/40 opacity-50 cursor-not-allowed"
              : "border-slate-200 hover:border-blue-400 bg-slate-50/60 hover:bg-blue-50/50"
          }`}
          title={
            selectedIndustryObj && selectedIndustryObj.qualified_leads === 0
              ? "Cannot export: 0 contact-qualified leads in this category"
              : `Export ${selectedCategory} leads with contact numbers`
          }
        >
          <div className="flex items-start justify-between gap-1.5 w-full">
            <div className="min-w-0 flex-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 block truncate">
                Selected Industry
              </span>
              <span className="text-xs font-bold text-slate-900 group-hover:text-blue-700 line-clamp-1 mt-0.5">
                Export {selectedCategory || "Industry"}
              </span>
            </div>
            {activeAction === "single" ? (
              <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
            ) : (
              <Download className="w-4 h-4 text-slate-400 group-hover:text-blue-600 shrink-0 transition-colors" />
            )}
          </div>
          <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
            <span>
              {selectedIndustryObj ? `${selectedIndustryObj.qualified_leads} eligible leads` : "Ready"}
            </span>
            <span className="font-mono text-[10px] text-slate-400 uppercase">
              .{fileFormat}
            </span>
          </div>
        </button>

        {/* Action 2: Export All Industries Separately (ZIP) */}
        <button
          type="button"
          disabled={isExporting || totalEligibleAcrossAll === 0}
          onClick={() => handleExportTrigger("all_separate_zip", "zip")}
          className="p-3 rounded-xl border border-slate-200 hover:border-emerald-400 bg-slate-50/60 hover:bg-emerald-50/50 text-left transition flex flex-col justify-between group disabled:opacity-50 touch-manipulation min-h-[92px]"
          title="Packages separate files for each industry into india_leads_by_industry.zip"
        >
          <div className="flex items-start justify-between gap-1.5 w-full">
            <div className="min-w-0 flex-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block truncate">
                Separate Files in ZIP
              </span>
              <span className="text-xs font-bold text-slate-900 group-hover:text-emerald-800 line-clamp-1 mt-0.5">
                Export All Industries (.zip)
              </span>
            </div>
            {activeAction === "zip" ? (
              <Loader2 className="w-4 h-4 text-emerald-600 animate-spin shrink-0" />
            ) : (
              <Archive className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 shrink-0 transition-colors" />
            )}
          </div>
          <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
            <span>{eligibleIndustriesCount} industries • {totalEligibleAcrossAll} leads</span>
            <span className="font-mono text-[10px] text-slate-400">
              india_leads_by_industry.zip
            </span>
          </div>
        </button>

        {/* Action 3: Export All Leads Combined */}
        <button
          type="button"
          disabled={isExporting || totalEligibleAcrossAll === 0}
          onClick={() => handleExportTrigger("all_combined", "combined")}
          className="p-3 rounded-xl border border-slate-200 hover:border-indigo-400 bg-slate-50/60 hover:bg-indigo-50/50 text-left transition flex flex-col justify-between group disabled:opacity-50 touch-manipulation min-h-[92px]"
          title="Consolidates all contact-qualified leads into a single file"
        >
          <div className="flex items-start justify-between gap-1.5 w-full">
            <div className="min-w-0 flex-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 block truncate">
                Single Consolidated File
              </span>
              <span className="text-xs font-bold text-slate-900 group-hover:text-indigo-800 line-clamp-1 mt-0.5">
                Export All Leads Combined
              </span>
            </div>
            {activeAction === "combined" ? (
              <Loader2 className="w-4 h-4 text-indigo-600 animate-spin shrink-0" />
            ) : (
              <Layers className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 shrink-0 transition-colors" />
            )}
          </div>
          <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
            <span>{totalEligibleAcrossAll} leads combined</span>
            <span className="font-mono text-[10px] text-slate-400 uppercase">
              all_leads.{fileFormat}
            </span>
          </div>
        </button>
      </div>

      {/* Progress / Spinner Feedback */}
      {isExporting && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-800 flex items-center space-x-2">
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
          <span className="font-medium">
            Generating export with phonenumbers validation, formula sanitization, and ODbL attribution...
          </span>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2 min-w-0">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="truncate">{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-500 hover:text-rose-800 p-1"
            aria-label="Dismiss error"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Recent Success Export Notice */}
      {recentExport && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
          <div className="flex items-center space-x-2.5 min-w-0">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <div className="min-w-0">
              <div className="font-bold text-slate-900 truncate">
                {recentExport.filename || "export_file"}
              </div>
              <div className="text-[11px] text-slate-600">
                {recentExport.row_count} contact-qualified leads • {formatBytes(recentExport.file_size_bytes)}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {recentExport.download_url && (
              <a
                href={recentExport.download_url}
                download
                className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition shadow-2xs touch-manipulation"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Again</span>
              </a>
            )}
            <button
              onClick={() => setRecentExport(null)}
              className="text-slate-400 hover:text-slate-700 p-1"
              aria-label="Dismiss notice"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
