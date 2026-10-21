"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, MapPin, CheckCircle2, AlertCircle, Loader2, Info } from "lucide-react";
import { useCreateDiscoveryJob, useCategorySuggestions } from "@/hooks/use-jobs";
import { useLocationSuggestions } from "@/hooks/use-locations";
import { DiscoveryJob } from "@/types";

interface SearchFormProps {
  onJobCreated?: (job: DiscoveryJob) => void;
  activeJob?: DiscoveryJob | null;
  activeJobId?: string | null;
  isJobLoading?: boolean;
}

export function SearchForm({
  onJobCreated,
  activeJob,
  activeJobId,
  isJobLoading = false,
}: SearchFormProps = {}) {
  const router = useRouter();
  const [location, setLocation] = useState("Mohali");
  const [category, setCategory] = useState("Salon");
  const [maxLeads, setMaxLeads] = useState<number>(50);
  const [source, setSource] = useState("overpass");

  const [radiusKm, setRadiusKm] = useState<number>(15);

  // Filter checkboxes
  const [mustHavePhone, setMustHavePhone] = useState(false);
  const [mustHaveMobile, setMustHaveMobile] = useState(false);
  const [mustHaveEmail, setMustHaveEmail] = useState(false);
  const [mustHaveWebsite, setMustHaveWebsite] = useState(false);
  const [mustHaveWhatsapp, setMustHaveWhatsapp] = useState(false);
  const [excludeSaved, setExcludeSaved] = useState(false);

  // Autocomplete UI state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showCatSuggestions, setShowCatSuggestions] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const catWrapperRef = useRef<HTMLDivElement>(null);

  const { data: suggestions } = useLocationSuggestions(location);
  const { data: catSuggestions } = useCategorySuggestions(category);
  const { mutate: createJob, isPending } = useCreateDiscoveryJob();

  // Button lifecycle synchronization with backend discovery status
  const isStarting = isPending;
  const isProcessing = Boolean(
    (activeJobId && isJobLoading && !activeJob) ||
    (activeJob && ["pending", "queued", "running"].includes(activeJob.status))
  );
  const isDisabled = isStarting || isProcessing;

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
      if (catWrapperRef.current && !catWrapperRef.current.contains(event.target as Node)) {
        setShowCatSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isDisabled) return; // Prevent duplicate clicks or submissions
    setErrorMsg(null);

    if (!location.trim()) {
      setErrorMsg("Please enter an Indian city, district, state, or PIN code.");
      return;
    }
    if (!category.trim()) {
      setErrorMsg("Please enter a business category (e.g. Salon, Restaurant, IT Company).");
      return;
    }

    const trimmedLoc = location.trim();
    let locationsArray: string[] | undefined = undefined;
    if (trimmedLoc.includes("+") || trimmedLoc.includes(",") || trimmedLoc.includes(";")) {
      const delimiter = trimmedLoc.includes("+") ? "+" : trimmedLoc.includes(";") ? ";" : ",";
      const parts = trimmedLoc.split(delimiter).map((p) => p.trim()).filter(Boolean);
      if (parts.length > 1) {
        locationsArray = parts;
      }
    }

    createJob(
      {
        location: trimmedLoc,
        locations: locationsArray,
        category: category.trim(),
        max_leads: maxLeads,
        source: source,
        radius_km: radiusKm,
        must_have_phone: mustHavePhone,
        must_have_mobile: mustHaveMobile,
        must_have_email: mustHaveEmail,
        must_have_website: mustHaveWebsite,
        must_have_whatsapp: mustHaveWhatsapp,
        exclude_already_saved: excludeSaved,
      },
      {
        onSuccess: (job) => {
          if (onJobCreated) {
            onJobCreated(job);
          } else {
            router.push(`/jobs?active=${job.id}`);
          }
        },
        onError: (err: any) => {
          setErrorMsg(err.message || "Failed to initiate discovery search.");
        },
      }
    );
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-6 max-w-4xl mx-auto w-full min-w-0">
      <div className="mb-5 sm:mb-6">
        <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center">
          <Search className="w-5 h-5 text-blue-600 mr-2 shrink-0" />
          <span>Find Business Leads in India</span>
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Target verified business contacts, websites, phone numbers, and WhatsApp across Indian cities.
        </p>
      </div>

      {(errorMsg || (activeJob?.status === "failed" && activeJob.error_message)) && (
        <div className="mb-5 p-3.5 sm:p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs sm:text-sm flex items-start space-x-2.5">
          <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="min-w-0 flex-1">
            <div className="font-semibold">Search Execution Error</div>
            <div className="mt-0.5 break-words">{errorMsg || activeJob?.error_message}</div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5">
          {/* Location input with autocomplete */}
          <div className="relative" ref={wrapperRef}>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 sm:mb-2">
              Indian Location <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder="e.g. Mohali, Chandigarh, Bengaluru, 160062"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm placeholder:text-slate-400 min-h-[44px]"
              />
            </div>

            {/* Suggestions dropdown */}
            {showSuggestions && suggestions && suggestions.length > 0 && (
              <div className="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-56 overflow-y-auto">
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setLocation(s.city);
                      setShowSuggestions(false);
                    }}
                    className="w-full text-left px-3.5 py-2.5 text-xs text-slate-700 hover:bg-blue-50 hover:text-blue-700 flex items-center justify-between border-b border-slate-100 last:border-0"
                  >
                    <span className="font-medium truncate mr-2">{s.display_name}</span>
                    <span className="text-[10px] text-slate-400 uppercase shrink-0">India</span>
                  </button>
                ))}
              </div>
            )}

            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] text-slate-400 font-medium">Multi-City Clusters:</span>
              <button
                type="button"
                onClick={() => {
                  setLocation("Chandigarh + Mohali + Panchkula");
                  setShowSuggestions(false);
                }}
                className="text-[11px] bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 px-2.5 py-1 rounded-md transition touch-manipulation"
              >
                Chandigarh + Mohali + Panchkula (Tricity)
              </button>
              <button
                type="button"
                onClick={() => {
                  setLocation("Delhi + Noida + Gurugram");
                  setShowSuggestions(false);
                }}
                className="text-[11px] bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 px-2.5 py-1 rounded-md transition touch-manipulation"
              >
                Delhi + Noida + Gurugram (NCR)
              </button>
            </div>
            <span className="text-[11px] text-slate-400 mt-1.5 block leading-normal">
              Enter Indian cities (single or multi-city separated by &apos;+&apos; or commas). Overlapping search areas are deduplicated automatically.
            </span>
          </div>

          {/* Business Category input with taxonomy suggestions */}
          <div className="relative" ref={catWrapperRef}>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 sm:mb-2">
              Business Category / Industry <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setShowCatSuggestions(true);
              }}
              onFocus={() => setShowCatSuggestions(true)}
              placeholder="e.g. Pet Shop, Salon, Clinic, Gym, Cafe"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm placeholder:text-slate-400 min-h-[44px]"
            />

            {/* Category Suggestions Dropdown */}
            {showCatSuggestions && catSuggestions && catSuggestions.length > 0 && (
              <div className="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-60 overflow-y-auto divide-y divide-slate-100">
                {catSuggestions.map((s, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setCategory(s.canonical_name);
                      setShowCatSuggestions(false);
                    }}
                    className="w-full text-left px-3.5 py-2.5 hover:bg-blue-50/70 transition-colors flex flex-col"
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="font-semibold text-xs text-slate-800">{s.canonical_name}</span>
                      <span className="text-[10px] text-blue-600 bg-blue-50 font-medium px-1.5 py-0.5 rounded">Supported</span>
                    </div>
                    {s.description && (
                      <span className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">{s.description}</span>
                    )}
                    {s.sample_aliases && s.sample_aliases.length > 0 && (
                      <span className="text-[10px] text-slate-400 mt-0.5">
                        Includes: {s.sample_aliases.slice(0, 3).join(", ")}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}

            <span className="text-[11px] text-slate-400 mt-1.5 block leading-normal">
              Enter any supported commercial category (e.g. Pet Shop, Gym, Clinic, Salon).
            </span>
          </div>
        </div>

        {/* Max Leads, Search Radius & Source Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-5 pt-2 border-t border-slate-100">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 sm:mb-2">
              Maximum Leads
            </label>
            <select
              value={maxLeads}
              onChange={(e) => setMaxLeads(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value={25}>25 leads</option>
              <option value={50}>50 leads (Recommended)</option>
              <option value={100}>100 leads</option>
              <option value={250}>250 leads</option>
              <option value={500}>500 leads</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 sm:mb-2">
              Geographic Radius
            </label>
            <select
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value={10}>10 km (Municipal / City Core)</option>
              <option value={15}>15 km (Greater Urban / Tricity)</option>
              <option value={25}>25 km (Metropolitan Urban Area)</option>
              <option value={50}>50 km (Regional District Area)</option>
            </select>
          </div>

          <div className="sm:col-span-2 md:col-span-1">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 sm:mb-2">
              Data Discovery Mode
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value="overpass">OpenStreetMap Overpass (Live Real Data)</option>
              <option value="google_places">Google Places API (Preview)</option>
            </select>
          </div>
        </div>

        {/* Geographic Radius & Provenance Disclosure */}
        <div className="p-3 sm:p-3.5 bg-blue-50/70 rounded-lg border border-blue-100 flex items-start space-x-2.5 text-xs text-blue-900">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold">Geographic Radius &amp; Provenance Disclosure: </span>
            The Overpass API queries real commercial business records within a {radiusKm} km radius of the resolved Indian location center coordinates. Data is sourced from OpenStreetMap contributors under ODbL 1.0 with complete source provenance. Results reflect genuine businesses mapped in OSM within this radius.
          </div>
        </div>

        {/* Optional Filters */}
        <div className="pt-2 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2.5 sm:mb-3">
            Contact Enrichment Requirements
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 sm:gap-3">
            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer touch-manipulation py-1">
              <input
                type="checkbox"
                checked={mustHavePhone}
                onChange={(e) => setMustHavePhone(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
              />
              <span>Must have phone</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer touch-manipulation py-1">
              <input
                type="checkbox"
                checked={mustHaveMobile}
                onChange={(e) => setMustHaveMobile(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
              />
              <span>Must have mobile number</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer touch-manipulation py-1">
              <input
                type="checkbox"
                checked={mustHaveEmail}
                onChange={(e) => setMustHaveEmail(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
              />
              <span>Must have email</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer touch-manipulation py-1">
              <input
                type="checkbox"
                checked={mustHaveWebsite}
                onChange={(e) => setMustHaveWebsite(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
              />
              <span>Must have website</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer touch-manipulation py-1">
              <input
                type="checkbox"
                checked={mustHaveWhatsapp}
                onChange={(e) => setMustHaveWhatsapp(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
              />
              <span>Must have WhatsApp</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer touch-manipulation py-1">
              <input
                type="checkbox"
                checked={excludeSaved}
                onChange={(e) => setExcludeSaved(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 shrink-0"
              />
              <span>Exclude already saved</span>
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t border-slate-100 flex flex-col-reverse sm:flex-row sm:items-center justify-between gap-3">
          <div className="text-xs text-slate-500 flex items-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-1.5 shrink-0" />
            <span>Global branch deduplication automatically active</span>
          </div>

          <button
            type="submit"
            disabled={isDisabled}
            className="w-full sm:w-auto px-6 py-3 sm:py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg shadow-sm shadow-blue-500/20 transition-colors flex items-center justify-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed min-h-[44px] touch-manipulation"
          >
            {isStarting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                <span>Starting...</span>
              </>
            ) : isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4 shrink-0" />
                <span>Find Real Leads</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
