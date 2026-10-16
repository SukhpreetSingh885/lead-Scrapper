"use client";

import React, { useState } from "react";
import {
  CopyX,
  Check,
  Split,
  Trash2,
  AlertCircle,
  Building2,
  MapPin,
  Phone,
  Globe,
  Loader2,
} from "lucide-react";
import { DuplicateCandidate } from "@/types";
import { formatPhoneNumber } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useResolveDuplicate } from "@/hooks/use-duplicates";

interface DuplicateReviewCardProps {
  candidate: DuplicateCandidate;
}

export function DuplicateReviewCard({ candidate }: DuplicateReviewCardProps) {
  const [notes, setNotes] = useState("");
  const { mutate: resolve, isPending } = useResolveDuplicate();

  const existing = candidate.existing_branch;
  const incoming = candidate.candidate_branch;

  const handleAction = (resolution: "merge" | "keep_distinct" | "reject_candidate") => {
    resolve({
      candidateId: candidate.id,
      resolution,
      notes: notes || undefined,
    });
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      {/* Header with similarity score badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <CopyX className="w-5 h-5 text-amber-500" />
          <span className="font-bold text-slate-900 text-sm">
            Potential Duplicate Candidate
          </span>
          <Badge variant="warning" className="text-xs">
            {(candidate.match_score * 100).toFixed(0)}% Similarity
          </Badge>
        </div>

        <div className="text-xs text-slate-400">
          Detected across global branch registry
        </div>
      </div>

      {/* Supporting Evidence Signals */}
      <div className="bg-amber-50/60 border border-amber-200/80 rounded-lg p-3 text-xs text-amber-900">
        <div className="font-semibold flex items-center mb-1">
          <AlertCircle className="w-3.5 h-3.5 mr-1 text-amber-600" />
          Matching Signals & Supporting Evidence:
        </div>
        <ul className="list-disc list-inside space-y-0.5 text-slate-700">
          {candidate.match_reasons.map((reason, idx) => (
            <li key={idx}>{reason}</li>
          ))}
        </ul>
      </div>

      {/* Side-by-Side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Existing Branch */}
        <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">
              Existing Record (Database)
            </span>
            <Badge variant="secondary" className="text-[10px]">Active</Badge>
          </div>

          <div className="font-bold text-slate-900 text-sm">
            {existing?.business_name || "Unknown Business"}
          </div>

          <div className="text-slate-600 space-y-1">
            <div className="flex items-start space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
              <span>
                {existing?.address_line || "No address"}, {existing?.locality && `${existing.locality}, `}
                {existing?.city}, {existing?.state} {existing?.pincode}
              </span>
            </div>

            {existing?.primary_mobile && (
              <div className="flex items-center space-x-1.5">
                <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="font-mono">{formatPhoneNumber(existing.primary_mobile)}</span>
              </div>
            )}

            {existing?.website_url && (
              <div className="flex items-center space-x-1.5">
                <Globe className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{existing.website_url}</span>
              </div>
            )}
          </div>
        </div>

        {/* Candidate Branch */}
        <div className="p-4 rounded-lg border border-blue-200 bg-blue-50/30 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase text-blue-600 tracking-wider">
              Incoming Candidate
            </span>
            <Badge variant="warning" className="text-[10px]">Under Review</Badge>
          </div>

          <div className="font-bold text-slate-900 text-sm">
            {incoming?.business_name || "Unknown Business"}
          </div>

          <div className="text-slate-600 space-y-1">
            <div className="flex items-start space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
              <span>
                {incoming?.address_line || "No address"}, {incoming?.locality && `${incoming.locality}, `}
                {incoming?.city}, {incoming?.state} {incoming?.pincode}
              </span>
            </div>

            {incoming?.primary_mobile && (
              <div className="flex items-center space-x-1.5">
                <Phone className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="font-mono">{formatPhoneNumber(incoming.primary_mobile)}</span>
              </div>
            )}

            {incoming?.website_url && (
              <div className="flex items-center space-x-1.5">
                <Globe className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="truncate">{incoming.website_url}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Resolution Notes & Actions */}
      <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <input
          type="text"
          placeholder="Optional resolution notes (e.g. verified distinct franchise outlet)..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 w-full sm:max-w-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
        />

        <div className="flex items-center space-x-2">
          {/* Keep Distinct Button */}
          <button
            onClick={() => handleAction("keep_distinct")}
            disabled={isPending}
            className="px-3 py-1.5 rounded-lg border border-emerald-300 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 font-semibold text-xs flex items-center space-x-1 transition-colors"
            title="Confirm this is a separate branch outlet (e.g. Phase 7 vs Phase 3B2)"
          >
            <Split className="w-3.5 h-3.5 text-emerald-600" />
            <span>Keep as Distinct Branch</span>
          </button>

          {/* Merge Duplicate Button */}
          <button
            onClick={() => handleAction("merge")}
            disabled={isPending}
            className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center space-x-1 transition-colors shadow-sm"
            title="Merge into existing branch record and update contacts"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Confirm Duplicate (Merge)</span>
          </button>
        </div>
      </div>
    </div>
  );
}

