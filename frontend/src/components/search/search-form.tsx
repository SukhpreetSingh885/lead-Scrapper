"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, MapPin, Filter, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useCreateDiscoveryJob } from "@/hooks/use-jobs";
import { useLocationSuggestions, useValidateLocation } from "@/hooks/use-locations";

export function SearchForm() {
  const router = useRouter();
  const [location, setLocation] = useState("Mohali");
  const [category, setCategory] = useState("Salon");
  const [maxLeads, setMaxLeads] = useState<number>(50);
  const [source, setSource] = useState("auto");

  // Filter checkboxes
  const [mustHavePhone, setMustHavePhone] = useState(false);
  const [mustHaveMobile, setMustHaveMobile] = useState(false);
  const [mustHaveEmail, setMustHaveEmail] = useState(false);
  const [mustHaveWebsite, setMustHaveWebsite] = useState(false);
  const [mustHaveWhatsapp, setMustHaveWhatsapp] = useState(false);
  const [excludeSaved, setExcludeSaved] = useState(false);

  // Autocomplete UI state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const { data: suggestions } = useLocationSuggestions(location);
  const { mutate: createJob, isPending } = useCreateDiscoveryJob();

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!location.trim()) {
      setErrorMsg("Please enter an Indian city, district, state, or PIN code.");
      return;
    }
    if (!category.trim()) {
      setErrorMsg("Please enter a business category (e.g. Salon, Restaurant, IT Company).");
      return;
    }

    createJob(
      {
        location: location.trim(),
        category: category.trim(),
        max_leads: maxLeads,
        source: source,
        must_have_phone: mustHavePhone,
        must_have_mobile: mustHaveMobile,
        must_have_email: mustHaveEmail,
        must_have_website: mustHaveWebsite,
        must_have_whatsapp: mustHaveWhatsapp,
        exclude_already_saved: excludeSaved,
      },
      {
        onSuccess: (job) => {
          router.push(`/jobs?active=${job.id}`);
        },
        onError: (err: any) => {
          setErrorMsg(err.message || "Failed to initiate discovery search.");
        },
      }
    );
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center">
          <Search className="w-5 h-5 text-blue-600 mr-2" />
          Find Business Leads in India
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Target verified business contacts, websites, phone numbers, and WhatsApp across Indian cities.
        </p>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start space-x-2.5">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Search Validation Error</div>
            <div className="mt-0.5">{errorMsg}</div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Location input with autocomplete */}
          <div className="relative" ref={wrapperRef}>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
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
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm placeholder:text-slate-400"
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
                    className="w-full text-left px-3.5 py-2 text-xs text-slate-700 hover:bg-blue-50 hover:text-blue-700 flex items-center justify-between border-b border-slate-100 last:border-0"
                  >
                    <span className="font-medium">{s.display_name}</span>
                    <span className="text-[10px] text-slate-400 uppercase">India</span>
                  </button>
                ))}
              </div>
            )}
            <span className="text-[11px] text-slate-400 mt-1 block">
              Only Indian cities, states, districts, and PIN codes are supported.
            </span>
          </div>

          {/* Business Category input */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Business Category / Industry <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. Salon, Restaurant, Digital Marketing, Hotel"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm placeholder:text-slate-400"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Enter any commercial industry or business category.
            </span>
          </div>
        </div>

        {/* Max Leads & Source Selector */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2 border-t border-slate-100">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Maximum Leads
            </label>
            <select
              value={maxLeads}
              onChange={(e) => setMaxLeads(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={25}>25 leads</option>
              <option value={50}>50 leads (Recommended)</option>
              <option value={100}>100 leads</option>
              <option value={250}>250 leads</option>
              <option value={500}>500 leads</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Data Discovery Mode
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-slate-900 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="auto">Auto / Deterministic Demo Mode (Zero Credentials)</option>
              <option value="demo_fixture">Deterministic Demo Fixtures Only</option>
              <option value="google_places">Google Places API (Live Discovery Preview)</option>
            </select>
          </div>
        </div>

        {/* Optional Filters */}
        <div className="pt-2 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
            Contact Enrichment Requirements
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={mustHavePhone}
                onChange={(e) => setMustHavePhone(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <span>Must have phone</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={mustHaveMobile}
                onChange={(e) => setMustHaveMobile(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <span>Must have mobile number</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={mustHaveEmail}
                onChange={(e) => setMustHaveEmail(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <span>Must have email</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={mustHaveWebsite}
                onChange={(e) => setMustHaveWebsite(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <span>Must have website</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={mustHaveWhatsapp}
                onChange={(e) => setMustHaveWhatsapp(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <span>Must have WhatsApp</span>
            </label>

            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={excludeSaved}
                onChange={(e) => setExcludeSaved(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <span>Exclude already saved</span>
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="text-xs text-slate-500 flex items-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-1.5" />
            Global branch deduplication automatically active
          </div>

          <button
            type="submit"
            disabled={isPending}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg shadow-sm shadow-blue-500/20 transition-colors flex items-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating Search Job...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Find Leads</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

