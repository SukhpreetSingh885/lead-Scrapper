"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  MapPin,
  Phone,
  Mail,
  Globe,
  MessageSquare,
  ShieldCheck,
  RotateCw,
  ExternalLink,
  Calendar,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { useLeadDetail, useEnrichLead } from "@/hooks/use-leads";
import { formatPhoneNumber, formatDate } from "@/lib/utils";

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params.id as string;

  const { data: lead, isLoading, error } = useLeadDetail(leadId);
  const { mutate: enrich, isPending: isEnriching } = useEnrichLead();

  if (isLoading) {
    return (
      <div className="py-20 text-center text-slate-500 space-y-2">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-3 border-blue-600 border-t-transparent"></div>
        <div className="text-sm font-medium">Loading lead branch details...</div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="py-16 text-center space-y-4">
        <div className="text-base font-bold text-slate-800">Lead branch not found</div>
        <Link
          href="/leads"
          className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Leads</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back button */}
      <div>
        <button
          onClick={() => router.back()}
          className="inline-flex items-center space-x-1 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Leads</span>
        </button>
      </div>

      {/* Main Business Profile Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold text-slate-900">{lead.business_name}</h1>
              {lead.is_demo && <Badge variant="demo">DEMO DATA</Badge>}
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <span className="font-medium text-slate-700">{lead.category}</span>
              <span>•</span>
              <span>Company: {lead.legal_name}</span>
            </div>
          </div>

          {/* Website Enrichment Action */}
          <div className="shrink-0 flex items-center space-x-2">
            <button
              onClick={() => enrich(lead.id)}
              disabled={isEnriching || !lead.website_url}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-sm flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isEnriching ? "animate-spin" : ""}`} />
              <span>{isEnriching ? "Enriching Website..." : "Enrich Contacts"}</span>
            </button>
          </div>
        </div>

        {/* Location & Address */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div className="space-y-3">
            <div className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
              Physical Location (Republic of India)
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-start space-x-2">
                <MapPin className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="font-medium text-slate-900">
                    {lead.address_line || "Street address not available"}
                  </div>
                  {lead.locality && <div className="text-slate-600">Locality: {lead.locality}</div>}
                  <div className="text-slate-700 font-semibold">
                    {lead.city}, {lead.state} {lead.pincode && `- ${lead.pincode}`}
                  </div>
                  <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">
                    Country: India 🇮🇳
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Website & Domain */}
          <div className="space-y-3">
            <div className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
              Web Presence
            </div>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-start space-x-2">
                <Globe className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  {lead.website_url ? (
                    <a
                      href={lead.website_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline font-medium inline-flex items-center space-x-1"
                    >
                      <span>{lead.website_url}</span>
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  ) : (
                    <span className="text-slate-400 italic">No website available</span>
                  )}
                  {lead.website_domain && (
                    <div className="text-slate-500 text-[11px]">Domain: {lead.website_domain}</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Contacts Section */}
        <div className="space-y-3 border-t border-slate-100 pt-5">
          <div className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
            Verified Business Contacts ({lead.contacts.length})
          </div>

          {lead.contacts.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {lead.contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                      {contact.contact_type}
                    </span>
                    {contact.is_verified && (
                      <Badge variant="success" className="text-[9px] py-0 px-1">
                        Verified
                      </Badge>
                    )}
                  </div>

                  <div className="font-semibold text-slate-900 text-xs font-mono">
                    {contact.contact_type === "mobile" || contact.contact_type === "landline" || contact.contact_type === "whatsapp"
                      ? formatPhoneNumber(contact.normalized_value)
                      : contact.normalized_value}
                  </div>

                  <div className="text-[10px] text-slate-400">
                    Source: {contact.source}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-xl border border-dashed border-slate-200 text-center text-xs text-slate-400">
              No contacts discovered yet. Click "Enrich Contacts" to crawl the business website.
            </div>
          )}
        </div>

        {/* Social Profiles */}
        {lead.social_profiles && lead.social_profiles.length > 0 && (
          <div className="space-y-3 border-t border-slate-100 pt-5">
            <div className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
              Public Social Profiles
            </div>
            <div className="flex flex-wrap gap-2.5">
              {lead.social_profiles.map((soc) => (
                <a
                  key={soc.id}
                  href={soc.profile_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-400 bg-white text-xs font-medium text-slate-700 hover:text-blue-600 transition-colors flex items-center space-x-1.5 shadow-2xs"
                >
                  <span className="capitalize font-semibold">{soc.platform}</span>
                  {soc.handle && <span className="text-slate-400 text-[11px]">({soc.handle})</span>}
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Provenance & License Metadata */}
        <div className="border-t border-slate-100 pt-5 text-xs text-slate-500 space-y-2">
          <div className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
            Provenance & License Metadata
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl">
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Source</span>
              <span className="text-slate-800 font-medium">{lead.source_name || "Independently Verified"}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Permission Status</span>
              <span className="text-slate-800 font-medium">{lead.source_permission_status}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Confidence Score</span>
              <span className="text-slate-800 font-medium">{(lead.confidence_score * 100).toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Enrichment Status</span>
              <span className="text-slate-800 font-medium capitalize">{lead.enrichment_status}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

