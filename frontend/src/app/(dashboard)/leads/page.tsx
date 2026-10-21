"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { LeadsTable } from "@/components/leads/leads-table";
import { IndustryExportPanel } from "@/components/exports/industry-export-panel";
import { useLeads, useDashboardMetrics } from "@/hooks/use-leads";
import { Filter, X, RotateCcw, PhoneCall, Building2, MapPin, Briefcase, Database } from "lucide-react";

function LeadsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [searchQuery, setSearchQuery] = useState("");

  // Filters from URL
  const filterCity = searchParams.get("city") || "";
  const filterCategory = searchParams.get("category") || "";
  const filterJobId = searchParams.get("job_id") || "";
  const hasContactNumber = searchParams.get("has_contact_number") === "true";
  const hasMobile = searchParams.get("has_mobile") === "true";
  const hasEmail = searchParams.get("has_email") === "true";
  const hasWebsite = searchParams.get("has_website") === "true";
  const hasWhatsapp = searchParams.get("has_whatsapp") === "true";

  // Local input buffers
  const [cityInput, setCityInput] = useState(filterCity);
  const [categoryInput, setCategoryInput] = useState(filterCategory);

  useEffect(() => {
    setCityInput(filterCity);
  }, [filterCity]);

  useEffect(() => {
    setCategoryInput(filterCategory);
  }, [filterCategory]);

  const updateFilters = (newParams: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, val] of Object.entries(newParams)) {
      if (val === null || val === "" || val === "false") {
        params.delete(key);
      } else {
        params.set(key, val);
      }
    }
    setPage(1);
    router.push(`/leads?${params.toString()}`);
  };

  const resetAllFilters = () => {
    setCityInput("");
    setCategoryInput("");
    setSearchQuery("");
    setPage(1);
    router.push("/leads");
  };

  const { data: metrics } = useDashboardMetrics();

  const { data, isLoading } = useLeads({
    page,
    page_size: pageSize,
    query: searchQuery || undefined,
    city: filterCity || undefined,
    category: filterCategory || undefined,
    job_id: filterJobId || undefined,
    has_contact_number: hasContactNumber || undefined,
    has_mobile: hasMobile || undefined,
    has_email: hasEmail || undefined,
    has_website: hasWebsite || undefined,
    has_whatsapp: hasWhatsapp || undefined,
  });

  const hasActiveFilters = Boolean(
    filterCity ||
    filterCategory ||
    filterJobId ||
    hasContactNumber ||
    hasMobile ||
    hasEmail ||
    hasWebsite ||
    hasWhatsapp ||
    searchQuery
  );

  return (
    <div className="space-y-5 sm:space-y-6 max-w-7xl mx-auto w-full min-w-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <Header
            title="Saved Business Leads"
            subtitle="Explore, filter, and export verified Indian business branches and contacts saved in CRM."
          />
        </div>
        {filterJobId && (
          <div className="flex items-center space-x-2 bg-blue-50 border border-blue-200 text-blue-800 text-xs px-3 py-1.5 rounded-lg shrink-0">
            <Briefcase className="w-4 h-4 text-blue-600 shrink-0" />
            <span className="font-semibold">Search Job Isolation</span>
            <span className="text-blue-500 font-mono">({filterJobId.slice(0, 8)})</span>
            <button
              onClick={() => updateFilters({ job_id: null })}
              className="ml-1 p-0.5 text-blue-500 hover:text-blue-900 hover:bg-blue-100 rounded transition-colors touch-manipulation"
              title="Clear Search Job filter (Show All Saved Leads)"
              aria-label="Clear Search Job filter"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Database Metrics Overview Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center space-x-1.5">
          <Database className="w-3.5 h-3.5 text-blue-600 shrink-0" />
          <span>Global CRM Database Overview (All Saved Leads)</span>
        </div>
        {hasActiveFilters && (
          <div className="text-xs text-blue-800 bg-blue-50 border border-blue-200 px-3 py-1 rounded-lg font-medium inline-flex items-center space-x-1.5 self-start sm:self-auto">
            <span>Filtered Table:</span>
            <span className="font-bold text-blue-900">{data?.total ?? 0}</span>
            <span className="text-blue-600">matching of</span>
            <span className="font-bold text-blue-900">{metrics?.total_saved_leads ?? metrics?.total_unique_leads ?? 0}</span>
            <span className="text-blue-600">saved in database</span>
          </div>
        )}
      </div>

      {/* Database Metrics Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3">
        <div className="bg-white p-2.5 sm:p-3.5 rounded-xl border border-slate-200 shadow-2xs min-w-0">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider truncate">
            Total Saved Leads
          </div>
          <div className="text-lg sm:text-xl font-bold text-slate-900 mt-1 truncate">
            {metrics?.total_saved_leads ?? metrics?.total_unique_leads ?? 0}
          </div>
        </div>

        <div className="bg-white p-2.5 sm:p-3.5 rounded-xl border border-slate-200 shadow-2xs min-w-0">
          <div className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider truncate">
            With Mobile (+91)
          </div>
          <div className="text-lg sm:text-xl font-bold text-blue-700 mt-1 truncate">
            {metrics?.leads_with_mobile ?? 0}
          </div>
        </div>

        <div className="bg-white p-2.5 sm:p-3.5 rounded-xl border border-slate-200 shadow-2xs min-w-0">
          <div className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider truncate">
            With Phone / Landline
          </div>
          <div className="text-lg sm:text-xl font-bold text-slate-800 mt-1 truncate">
            {metrics?.leads_with_phone ?? 0}
          </div>
        </div>

        <div className="bg-white p-2.5 sm:p-3.5 rounded-xl border border-slate-200 shadow-2xs min-w-0">
          <div className="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider truncate">
            With WhatsApp
          </div>
          <div className="text-lg sm:text-xl font-bold text-emerald-700 mt-1 truncate">
            {metrics?.leads_with_whatsapp ?? 0}
          </div>
        </div>

        <div className="bg-white p-2.5 sm:p-3.5 rounded-xl border border-slate-200 shadow-2xs min-w-0">
          <div className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider truncate">
            Export-Eligible
          </div>
          <div className="text-lg sm:text-xl font-bold text-emerald-800 mt-1 truncate">
            {metrics?.export_eligible_leads ?? 0}
          </div>
        </div>

        <div className="bg-white p-2.5 sm:p-3.5 rounded-xl border border-slate-200 shadow-2xs min-w-0">
          <div className="text-[10px] font-semibold text-amber-700 uppercase tracking-wider truncate">
            Missing Phone
          </div>
          <div className="text-lg sm:text-xl font-bold text-amber-800 mt-1 truncate">
            {metrics?.leads_missing_contacts ?? 0}
          </div>
        </div>
      </div>

      {/* Industry-Wise Exports Panel */}
      <IndustryExportPanel initialCategory={filterCategory} />

      {/* Filter Toolbar */}
      <div className="bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-sm space-y-3 text-xs w-full min-w-0">
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center text-slate-700 font-semibold mr-1">
            <Filter className="w-3.5 h-3.5 mr-1.5 text-blue-600 shrink-0" />
            <span>Filters:</span>
          </div>

          {/* City filter input */}
          <div className="relative flex-1 sm:flex-initial min-w-[130px]">
            <MapPin className="w-3 h-3 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="City (e.g. Mohali)..."
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  updateFilters({ city: cityInput.trim() });
                }
              }}
              onBlur={() => {
                if (cityInput.trim() !== filterCity) {
                  updateFilters({ city: cityInput.trim() });
                }
              }}
              className="pl-7 pr-3 py-1.5 rounded-lg border border-slate-300 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full sm:w-36 text-xs min-h-[34px]"
            />
          </div>

          {/* Category filter input */}
          <div className="relative flex-1 sm:flex-initial min-w-[130px]">
            <Building2 className="w-3 h-3 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Category (e.g. Gym)..."
              value={categoryInput}
              onChange={(e) => setCategoryInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  updateFilters({ category: categoryInput.trim() });
                }
              }}
              onBlur={() => {
                if (categoryInput.trim() !== filterCategory) {
                  updateFilters({ category: categoryInput.trim() });
                }
              }}
              className="pl-7 pr-3 py-1.5 rounded-lg border border-slate-300 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full sm:w-36 text-xs min-h-[34px]"
            />
          </div>

          {/* Contact Qualification Filter Button */}
          <button
            onClick={() => updateFilters({ has_contact_number: hasContactNumber ? null : "true" })}
            className={`px-3 py-1.5 rounded-lg border font-semibold flex items-center space-x-1.5 transition-colors touch-manipulation min-h-[34px] ${
              hasContactNumber
                ? "bg-emerald-600 border-emerald-600 text-white shadow-2xs"
                : "border-slate-300 text-slate-700 hover:bg-slate-50"
            }`}
            title="Show only businesses with at least one verified phone/mobile/whatsapp number"
          >
            <PhoneCall className="w-3 h-3 shrink-0" />
            <span>Qualified Contacts</span>
          </button>

          {/* Mobile Filter */}
          <button
            onClick={() => updateFilters({ has_mobile: hasMobile ? null : "true" })}
            className={`px-3 py-1.5 rounded-lg border font-medium transition-colors touch-manipulation min-h-[34px] ${
              hasMobile
                ? "bg-blue-50 border-blue-300 text-blue-700"
                : "border-slate-300 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Mobile (+91)
          </button>

          {/* WhatsApp Filter */}
          <button
            onClick={() => updateFilters({ has_whatsapp: hasWhatsapp ? null : "true" })}
            className={`px-3 py-1.5 rounded-lg border font-medium transition-colors touch-manipulation min-h-[34px] ${
              hasWhatsapp
                ? "bg-blue-50 border-blue-300 text-blue-700"
                : "border-slate-300 text-slate-600 hover:bg-slate-50"
            }`}
          >
            WhatsApp
          </button>

          {/* Website Filter */}
          <button
            onClick={() => updateFilters({ has_website: hasWebsite ? null : "true" })}
            className={`px-3 py-1.5 rounded-lg border font-medium transition-colors touch-manipulation min-h-[34px] ${
              hasWebsite
                ? "bg-blue-50 border-blue-300 text-blue-700"
                : "border-slate-300 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Website
          </button>

          {/* Email Filter */}
          <button
            onClick={() => updateFilters({ has_email: hasEmail ? null : "true" })}
            className={`px-3 py-1.5 rounded-lg border font-medium transition-colors touch-manipulation min-h-[34px] ${
              hasEmail
                ? "bg-blue-50 border-blue-300 text-blue-700"
                : "border-slate-300 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Email
          </button>

          {/* Reset / View All Businesses Action */}
          {hasActiveFilters && (
            <button
              onClick={resetAllFilters}
              className="text-xs text-rose-600 hover:text-rose-800 font-semibold ml-auto flex items-center space-x-1 hover:underline touch-manipulation py-1"
            >
              <RotateCcw className="w-3 h-3 shrink-0" />
              <span>Reset Filters</span>
            </button>
          )}
        </div>

        {/* Active Filter Chips */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100 text-xs">
            <span className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider mr-1">Active:</span>

            {filterJobId && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 border border-blue-200 text-blue-800 text-[11px]">
                Search Job: {filterJobId.slice(0, 8)}
                <button
                  onClick={() => updateFilters({ job_id: null })}
                  className="ml-1 text-blue-400 hover:text-blue-800"
                  aria-label="Remove search job filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {filterCity && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-800 text-[11px]">
                City: {filterCity}
                <button
                  onClick={() => {
                    setCityInput("");
                    updateFilters({ city: null });
                  }}
                  className="ml-1 text-slate-400 hover:text-slate-800"
                  aria-label="Remove city filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {filterCategory && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-800 text-[11px]">
                Category: {filterCategory}
                <button
                  onClick={() => {
                    setCategoryInput("");
                    updateFilters({ category: null });
                  }}
                  className="ml-1 text-slate-400 hover:text-slate-800"
                  aria-label="Remove category filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {hasContactNumber && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px]">
                Contact Qualified Only
                <button
                  onClick={() => updateFilters({ has_contact_number: null })}
                  className="ml-1 text-emerald-600 hover:text-emerald-900"
                  aria-label="Remove contact qualified filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {hasMobile && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200 text-[11px]">
                Mobile Only
                <button
                  onClick={() => updateFilters({ has_mobile: null })}
                  className="ml-1 text-blue-600 hover:text-blue-900"
                  aria-label="Remove mobile filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {hasWhatsapp && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200 text-[11px]">
                WhatsApp Only
                <button
                  onClick={() => updateFilters({ has_whatsapp: null })}
                  className="ml-1 text-blue-600 hover:text-blue-900"
                  aria-label="Remove whatsapp filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {hasWebsite && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200 text-[11px]">
                Website Only
                <button
                  onClick={() => updateFilters({ has_website: null })}
                  className="ml-1 text-blue-600 hover:text-blue-900"
                  aria-label="Remove website filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {hasEmail && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200 text-[11px]">
                Email Only
                <button
                  onClick={() => updateFilters({ has_email: null })}
                  className="ml-1 text-blue-600 hover:text-blue-900"
                  aria-label="Remove email filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>
        )}
      </div>

      {/* Main Leads Table */}
      <LeadsTable
        leads={data?.items || []}
        total={data?.total || 0}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onSearchChange={setSearchQuery}
        isLoading={isLoading}
        filterCity={filterCity}
        filterCategory={filterCategory}
        filterJobId={filterJobId}
        hasContactNumber={hasContactNumber}
        onResetFilters={resetAllFilters}
        totalSavedLeads={metrics?.total_saved_leads ?? metrics?.total_unique_leads ?? 0}
      />
    </div>
  );
}

export default function LeadsPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-xs text-slate-400">Loading leads...</div>}>
      <LeadsContent />
    </Suspense>
  );
}
