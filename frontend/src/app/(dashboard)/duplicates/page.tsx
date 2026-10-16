"use client";

import React, { useState } from "react";
import { CopyX, CheckCircle, ShieldCheck } from "lucide-react";
import { Header } from "@/components/layout/header";
import { DuplicateReviewCard } from "@/components/duplicates/duplicate-review-card";
import { useDuplicateCandidates } from "@/hooks/use-duplicates";

export default function DuplicatesPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useDuplicateCandidates(page, 20);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <Header
        title="Duplicate Candidate Review"
        subtitle="Inspect uncertain branch matches across the database with confidence scoring and supporting evidence."
      />

      {/* Explanation Banner */}
      <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 text-xs flex items-start space-x-3">
        <ShieldCheck className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold">Branch Separation & Integrity Policy</div>
          <p className="text-[11px] leading-relaxed text-blue-800">
            Different branches of the same company (e.g. <em>ABC Salon — Phase 7, Mohali</em> vs{" "}
            <em>ABC Salon — Phase 3B2, Mohali</em>) are recognized as valid separate leads. Only
            uncertain name/address variations are quarantined here for manual review.
          </p>
        </div>
      </div>

      {/* Candidates List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent mb-2"></div>
            <div>Loading duplicate review queue...</div>
          </div>
        ) : data?.items && data.items.length > 0 ? (
          data.items.map((candidate) => (
            <DuplicateReviewCard key={candidate.id} candidate={candidate} />
          ))
        ) : (
          <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-500">
            <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <div className="font-semibold text-sm text-slate-800">
              No duplicate candidates pending review
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Your database is clean. All high-confidence duplicate branches were automatically updated, and distinct branches preserved.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

