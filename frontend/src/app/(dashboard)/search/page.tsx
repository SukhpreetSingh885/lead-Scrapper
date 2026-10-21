"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { SearchForm } from "@/components/search/search-form";
import { JobProgressCard } from "@/components/jobs/job-progress-card";
import { SearchPreviewTable } from "@/components/search/search-preview-table";
import { useDiscoveryJob } from "@/hooks/use-jobs";
import { Sparkles, MapPin, ArrowRight, CheckCircle2, RotateCw } from "lucide-react";
import Link from "next/link";
import { DiscoveryJob } from "@/types";

function SearchContent() {
  const searchParams = useSearchParams();
  const urlJobId = searchParams.get("job_id") || searchParams.get("active");
  const [activeJobId, setActiveJobId] = useState<string | null>(urlJobId);

  useEffect(() => {
    if (urlJobId) {
      setActiveJobId(urlJobId);
    }
  }, [urlJobId]);

  const { data: activeJob, isLoading: isJobLoading } = useDiscoveryJob(activeJobId || "");

  const handleJobCreated = (job: DiscoveryJob) => {
    setActiveJobId(job.id);
    if (typeof window !== "undefined") {
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.set("job_id", job.id);
      window.history.pushState(null, "", newUrl.toString());
    }
  };

  const exampleSearches = [
    { city: "Mohali", category: "Gym" },
    { city: "Mohali", category: "Salon" },
    { city: "Mohali", category: "Cafe" },
    { city: "Mohali", category: "Pet Shop" },
    { city: "Mohali", category: "Clinic" },
    { city: "Chandigarh", category: "Restaurant" },
    { city: "Delhi", category: "Real Estate Agents" },
    { city: "Ludhiana", category: "Manufacturers" },
    { city: "Mumbai", category: "Digital Marketing Agency" },
    { city: "Pune", category: "Software Companies" },
    { city: "Jaipur", category: "Hotels" },
    { city: "Bengaluru", category: "IT Companies" },
  ];

  return (
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto w-full min-w-0">
      <Header
        title="Find Business Leads"
        subtitle="Search dynamic business categories across Indian cities, districts, localities, and PIN codes."
      />

      <SearchForm
        onJobCreated={handleJobCreated}
        activeJob={activeJob}
        activeJobId={activeJobId}
        isJobLoading={isJobLoading}
      />

      {/* Loading state for linked job */}
      {activeJobId && isJobLoading && !activeJob && (
        <div className="p-8 bg-white border border-slate-200 rounded-xl text-center space-y-2">
          <RotateCw className="w-5 h-5 text-blue-600 animate-spin mx-auto" />
          <div className="text-xs text-slate-500">Loading discovery job {activeJobId}...</div>
        </div>
      )}

      {/* Active Search Results & Preview Section */}
      {activeJob && (
        <div className="space-y-4 pt-2 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-1.5 min-w-0">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="truncate">
                Search Results for {activeJob.category} in {activeJob.resolved_city}
              </span>
            </h3>
            <Link
              href={`/leads?category=${encodeURIComponent(activeJob.category)}&city=${encodeURIComponent(activeJob.resolved_city)}`}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1 shrink-0"
            >
              <span>View Saved Leads in CRM</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <JobProgressCard job={activeJob} defaultExpandedPreview={true} />
        </div>
      )}

      {/* Suggested Quick Searches */}
      <div className="bg-slate-100/70 rounded-xl p-4 sm:p-5 border border-slate-200">
        <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center">
          <Sparkles className="w-3.5 h-3.5 text-blue-600 mr-1.5 shrink-0" />
          <span>Example Dynamic Indian Searches (Click to fill)</span>
        </div>
        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {exampleSearches.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => {
                const locInput = document.querySelector('input[placeholder*="Mohali"]') as HTMLInputElement;
                const catInput = document.querySelector('input[placeholder*="Salon"]') as HTMLInputElement;
                if (locInput) {
                  locInput.value = ex.city;
                  locInput.dispatchEvent(new Event("input", { bubbles: true }));
                }
                if (catInput) {
                  catInput.value = ex.category;
                  catInput.dispatchEvent(new Event("input", { bubbles: true }));
                }
              }}
              className="px-2.5 sm:px-3 py-1.5 bg-white border border-slate-200 hover:border-blue-400 rounded-lg text-xs font-medium text-slate-700 hover:text-blue-600 transition-colors shadow-2xs flex items-center space-x-1.5 touch-manipulation"
            >
              <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
              <span>{ex.city}</span>
              <span className="text-slate-300">•</span>
              <span>{ex.category}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-xs text-slate-400">Loading search leads...</div>}>
      <SearchContent />
    </Suspense>
  );
}
