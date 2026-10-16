"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { LeadsTable } from "@/components/leads/leads-table";
import { useLeads } from "@/hooks/use-leads";
import { Filter } from "lucide-react";

function LeadsContent() {
  const searchParams = useSearchParams();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [searchQuery, setSearchQuery] = useState("");

  // Filters
  const [filterCity, setFilterCity] = useState(searchParams.get("city") || "");
  const [filterCategory, setFilterCategory] = useState(searchParams.get("category") || "");
  const [hasMobile, setHasMobile] = useState(searchParams.get("has_mobile") === "true");
  const [hasEmail, setHasEmail] = useState(searchParams.get("has_email") === "true");
  const [hasWebsite, setHasWebsite] = useState(searchParams.get("has_website") === "true");
  const [hasWhatsapp, setHasWhatsapp] = useState(searchParams.get("has_whatsapp") === "true");

  const { data, isLoading } = useLeads({
    page,
    page_size: pageSize,
    query: searchQuery || undefined,
    city: filterCity || undefined,
    category: filterCategory || undefined,
    has_mobile: hasMobile || undefined,
    has_email: hasEmail || undefined,
    has_website: hasWebsite || undefined,
    has_whatsapp: hasWhatsapp || undefined,
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <Header
        title="Business Leads Database"
        subtitle="Explore, filter, and export verified Indian business branches and contacts."
      />

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-3 text-xs">
        <div className="flex items-center text-slate-500 font-semibold mr-1">
          <Filter className="w-3.5 h-3.5 mr-1" />
          <span>Filters:</span>
        </div>

        <input
          type="text"
          placeholder="Filter city (e.g. Mohali)..."
          value={filterCity}
          onChange={(e) => {
            setFilterCity(e.target.value);
            setPage(1);
          }}
          className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 w-36"
        />

        <input
          type="text"
          placeholder="Filter category..."
          value={filterCategory}
          onChange={(e) => {
            setFilterCategory(e.target.value);
            setPage(1);
          }}
          className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 w-36"
        />

        <button
          onClick={() => {
            setHasMobile(!hasMobile);
            setPage(1);
          }}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
            hasMobile
              ? "bg-blue-50 border-blue-300 text-blue-700"
              : "border-slate-300 text-slate-600 hover:bg-slate-50"
          }`}
        >
          Has Mobile (+91)
        </button>

        <button
          onClick={() => {
            setHasEmail(!hasEmail);
            setPage(1);
          }}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
            hasEmail
              ? "bg-blue-50 border-blue-300 text-blue-700"
              : "border-slate-300 text-slate-600 hover:bg-slate-50"
          }`}
        >
          Has Email
        </button>

        <button
          onClick={() => {
            setHasWebsite(!hasWebsite);
            setPage(1);
          }}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
            hasWebsite
              ? "bg-blue-50 border-blue-300 text-blue-700"
              : "border-slate-300 text-slate-600 hover:bg-slate-50"
          }`}
        >
          Has Website
        </button>

        <button
          onClick={() => {
            setHasWhatsapp(!hasWhatsapp);
            setPage(1);
          }}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-colors ${
            hasWhatsapp
              ? "bg-blue-50 border-blue-300 text-blue-700"
              : "border-slate-300 text-slate-600 hover:bg-slate-50"
          }`}
        >
          Has WhatsApp
        </button>

        {(filterCity || filterCategory || hasMobile || hasEmail || hasWebsite || hasWhatsapp) && (
          <button
            onClick={() => {
              setFilterCity("");
              setFilterCategory("");
              setHasMobile(false);
              setHasEmail(false);
              setHasWebsite(false);
              setHasWhatsapp(false);
              setPage(1);
            }}
            className="text-xs text-rose-600 hover:underline font-semibold ml-auto"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Main Leads Table */}
      <LeadsTable
        leads={data?.items || []}
        total={data?.total || 0}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onSearchChange={(q) => {
          setSearchQuery(q);
          setPage(1);
        }}
        isLoading={isLoading}
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
