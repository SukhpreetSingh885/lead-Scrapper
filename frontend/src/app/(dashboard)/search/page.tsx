"use client";

import React from "react";
import { Header } from "@/components/layout/header";
import { SearchForm } from "@/components/search/search-form";
import { Sparkles, MapPin, Search } from "lucide-react";

export default function SearchPage() {
  const exampleSearches = [
    { city: "Mohali", category: "Salon" },
    { city: "Chandigarh", category: "Restaurant" },
    { city: "Delhi", category: "Real Estate Agents" },
    { city: "Ludhiana", category: "Manufacturers" },
    { city: "Mumbai", category: "Digital Marketing Agency" },
    { city: "Pune", category: "Software Companies" },
    { city: "Jaipur", category: "Hotels" },
    { city: "Bengaluru", category: "IT Companies" },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <Header
        title="Find Business Leads"
        subtitle="Search dynamic business categories across Indian cities, districts, localities, and PIN codes."
      />

      <SearchForm />

      {/* Suggested Quick Searches */}
      <div className="bg-slate-100/70 rounded-xl p-5 border border-slate-200">
        <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center">
          <Sparkles className="w-3.5 h-3.5 text-blue-600 mr-1.5" />
          Example Dynamic Indian Searches (Click to fill)
        </div>
        <div className="flex flex-wrap gap-2">
          {exampleSearches.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => {
                const locInput = document.querySelector('input[placeholder*="Mohali"]') as HTMLInputElement;
                const catInput = document.querySelector('input[placeholder*="Salon"]') as HTMLInputElement;
                if (locInput) locInput.value = ex.city;
                if (catInput) catInput.value = ex.category;
              }}
              className="px-3 py-1.5 bg-white border border-slate-200 hover:border-blue-400 rounded-lg text-xs font-medium text-slate-700 hover:text-blue-600 transition-colors shadow-2xs flex items-center space-x-1.5"
            >
              <MapPin className="w-3 h-3 text-slate-400" />
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

