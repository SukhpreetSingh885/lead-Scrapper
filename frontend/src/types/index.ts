export interface BusinessContact {
  id: string;
  contact_type: "mobile" | "landline" | "whatsapp" | "email";
  original_value: string;
  normalized_value: string;
  is_primary: boolean;
  is_verified: boolean;
  source: string;
}

export interface SocialProfile {
  id: string;
  platform: string;
  profile_url: string;
  handle?: string;
}

export interface LeadListItem {
  id: string;
  company_id: string;
  business_name: string;
  category: string;
  primary_mobile?: string;
  primary_landline?: string;
  primary_whatsapp?: string;
  primary_email?: string;
  website_url?: string;
  city: string;
  state: string;
  locality?: string;
  pincode?: string;
  address_line?: string;
  enrichment_status: "pending" | "running" | "completed" | "failed" | "not_applicable";
  source_name?: string;
  is_demo: boolean;
  social_profiles_count: number;
  created_at: string;
  updated_at: string;
}

export interface LeadBranchDetail {
  id: string;
  company_id: string;
  business_name: string;
  legal_name: string;
  category: string;
  description?: string;
  website_domain?: string;
  website_url?: string;
  address_line?: string;
  locality?: string;
  city: string;
  district?: string;
  state: string;
  pincode?: string;
  country: string;
  latitude?: number;
  longitude?: number;
  primary_mobile?: string;
  primary_landline?: string;
  primary_whatsapp?: string;
  primary_email?: string;
  contacts: BusinessContact[];
  social_profiles: SocialProfile[];
  source_name?: string;
  source_code?: string;
  source_permission_status: string;
  confidence_score: number;
  enrichment_status: string;
  last_checked_at?: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface DiscoveryJobItem {
  id: string;
  business_name: string;
  address?: string;
  phone?: string;
  website?: string;
  is_eligible_for_crm: boolean;
  is_saved?: boolean;
  is_already_saved?: boolean;
  rejection_reason?: string;
  created_at: string;
}

export interface CityDiscoveryStats {
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  radius_meters: number;
  raw_discovered: number;
  category_matched: number;
  duplicates_removed: number;
  unique_contributed: number;
  contact_qualified: number;
}

export interface DiscoveryJob {
  id: string;
  location_input: string;
  resolved_city: string;
  resolved_state: string;
  category: string;
  max_leads: number;
  source_code: string;
  status: "pending" | "queued" | "running" | "completed" | "partially_completed" | "failed" | "cancelled";
  total_discovered: number;
  total_eligible: number;
  total_contact_qualified?: number;
  total_mobile?: number;
  total_landline?: number;
  total_whatsapp?: number;
  total_missing_phone?: number;
  total_enriched?: number;
  total_enrichment_unavailable?: number;
  total_inserted: number;
  total_updated: number;
  total_duplicates_flagged: number;
  total_failed: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  items?: DiscoveryJobItem[];
  per_city_stats?: CityDiscoveryStats[];
}

export interface DuplicateCandidate {
  id: string;
  existing_branch_id: string;
  candidate_branch_id: string;
  match_score: number;
  match_reasons: string[];
  status: "pending_review" | "confirmed_duplicate" | "confirmed_distinct" | "resolved_merged";
  existing_branch?: LeadListItem;
  candidate_branch?: LeadListItem;
  resolution_notes?: string;
  created_at: string;
}

export interface LocationSuggestion {
  id?: number;
  city: string;
  state: string;
  district?: string;
  locality?: string;
  pincode?: string;
  display_name: string;
}

export interface LocationValidationResult {
  is_valid: boolean;
  resolved_city?: string;
  resolved_state?: string;
  resolved_district?: string;
  resolved_pincode?: string;
  ambiguous: boolean;
  candidates: LocationSuggestion[];
  message?: string;
}

export interface DiscoveryPreviewItem {
  id: string;
  job_id: string;
  business_name: string;
  category?: string;
  address?: string;
  city?: string;
  state?: string;
  phone?: string;
  mobile?: string;
  whatsapp?: string;
  email?: string;
  website?: string;
  is_eligible_for_crm: boolean;
  is_saved: boolean;
  is_already_saved: boolean;
  source?: string;
  source_code?: string;
  has_contact_number?: boolean;
  branch_id?: string;
  rejection_reason?: string;
  created_at: string;
}

export interface CategorySuggestion {
  canonical_name: string;
  slug: string;
  description: string;
  sample_aliases: string[];
  ambiguous_alternatives?: string[];
}

export interface SaveSelectedLeadsResponse {
  success: boolean;
  total_requested: number;
  saved_count: number;
  already_existing_count: number;
  skipped_count: number;
  failed_count: number;
  saved_lead_ids: string[];
  message: string;
}

export interface DeleteLeadsResponse {
  success: boolean;
  deleted_count: number;
  message: string;
}

export interface IndustryExportOption {
  category: string;
  slug: string;
  total_leads: number;
  qualified_leads: number;
}

export interface ExportItem {
  id: string;
  file_format: "csv" | "xlsx" | "zip";
  export_mode?: "single" | "all_combined" | "all_separate_zip";
  filename?: string;
  row_count: number;
  file_size_bytes: number;
  status: "pending" | "processing" | "ready" | "failed";
  download_url?: string;
  error_message?: string;
  created_at: string;
}

export interface DashboardMetrics {
  total_unique_leads: number;
  total_saved_leads?: number;
  leads_with_mobile: number;
  leads_with_phone?: number;
  leads_with_email: number;
  leads_with_website: number;
  leads_with_whatsapp: number;
  export_eligible_leads?: number;
  leads_missing_contacts?: number;
  duplicate_candidates: number;
  active_jobs: number;
  completed_jobs: number;
  demo_leads_count: number;
  live_leads_count: number;
  is_demo_mode_active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

