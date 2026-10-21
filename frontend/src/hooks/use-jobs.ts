"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { DiscoveryJob, PaginatedResponse } from "@/types";

export function useDiscoveryJobs(page: number = 1, pageSize: number = 20) {
  return useQuery<PaginatedResponse<DiscoveryJob>>({
    queryKey: ["discovery-jobs", page, pageSize],
    queryFn: () =>
      apiClient<PaginatedResponse<DiscoveryJob>>("/api/v1/discovery/jobs", {
        params: { page, page_size: pageSize },
      }),
    refetchInterval: (query) => {
      // Auto-poll if any job is currently pending or running
      const hasRunning = query.state.data?.items.some((j) =>
        ["pending", "queued", "running"].includes(j.status)
      );
      return hasRunning ? 2000 : 15000;
    },
  });
}

export function useDiscoveryJob(jobId: string) {
  return useQuery<DiscoveryJob>({
    queryKey: ["discovery-job", jobId],
    queryFn: () => apiClient<DiscoveryJob>(`/api/v1/discovery/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ["pending", "queued", "running"].includes(status) ? 2000 : false;
    },
  });
}

export function useCreateDiscoveryJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobData: {
      location: string;
      locations?: string[];
      category: string;
      max_leads: number;
      source?: string;
      must_have_phone?: boolean;
      must_have_mobile?: boolean;
      must_have_email?: boolean;
      must_have_website?: boolean;
      must_have_whatsapp?: boolean;
      exclude_already_saved?: boolean;
      radius_km?: number;
    }) =>
      apiClient<DiscoveryJob>("/api/v1/discovery/jobs", {
        method: "POST",
        body: JSON.stringify(jobData),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["discovery-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

export function useDiscoveryJobPreview(
  jobId: string,
  page: number = 1,
  pageSize: number = 50,
  filters?: {
    must_have_phone?: boolean;
    must_have_mobile?: boolean;
    must_have_landline?: boolean;
    must_have_email?: boolean;
    must_have_website?: boolean;
    must_have_whatsapp?: boolean;
    exclude_already_saved?: boolean;
  },
  enabled: boolean = true
) {
  return useQuery<PaginatedResponse<import("@/types").DiscoveryPreviewItem>>({
    queryKey: ["discovery-job-preview", jobId, page, pageSize, filters],
    queryFn: () =>
      apiClient<PaginatedResponse<import("@/types").DiscoveryPreviewItem>>(
        `/api/v1/discovery/jobs/${jobId}/preview`,
        {
          params: {
            page,
            page_size: pageSize,
            ...filters,
          },
        }
      ),
    enabled: Boolean(jobId) && enabled,
    refetchInterval: (query) => {
      // If no items yet, check every 2.5 seconds
      const count = query.state.data?.items?.length || 0;
      return count === 0 ? 2500 : false;
    },
  });
}

export function useSaveSelectedLeads() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { job_id: string; item_ids?: string[]; save_all_eligible?: boolean }) =>
      apiClient<import("@/types").SaveSelectedLeadsResponse>("/api/v1/leads/save-selected", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["discovery-job-preview", variables.job_id] });
      queryClient.invalidateQueries({ queryKey: ["discovery-job", variables.job_id] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

export function useCategorySuggestions(query: string) {
  return useQuery<import("@/types").CategorySuggestion[]>({
    queryKey: ["category-suggestions", query],
    queryFn: () => apiClient<import("@/types").CategorySuggestion[]>("/api/v1/discovery/categories/suggestions", {
      params: { q: query },
    }),
    staleTime: 60000,
  });
}

export function useDeleteDiscoveryJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      apiClient<{ success: boolean; message: string; deleted_job_id: string }>(
        `/api/v1/discovery/jobs/${jobId}`,
        {
          method: "DELETE",
        }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["discovery-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["discovery-job"] });
    },
  });
}

export function useClearJobPreview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      apiClient<{ success: boolean; message: string; cleared_count: number; remaining_items: number }>(
        `/api/v1/discovery/jobs/${jobId}/preview`,
        {
          method: "DELETE",
        }
      ),
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: ["discovery-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["discovery-job", jobId] });
      queryClient.invalidateQueries({ queryKey: ["discovery-job-preview", jobId] });
    },
  });
}


